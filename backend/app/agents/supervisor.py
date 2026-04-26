"""
backend/app/agents/supervisor.py
=================================

Orquestador central del agente Havi.

Topología del grafo:

    START
       │
       ▼
   FichaInjector  (lee Redis: ficha:{user_id})
       │
       ▼
    Guardrail     (seguridad)
       │
       ├─ block ─► Summarizer (respuesta canned)
       │
       ▼
    Profiler      (combina ficha + texto del usuario)
       │
       ▼
    Router        (decide team)
       │
       ├─► Research team
       │      ├─ plan_research
       │      ├─ gather_context
       │      └─ draft_research_response
       │
       └─► ToolOps team
              └─ run_tool_ops
       │
       ▼
    Summarizer    (síntesis final)
       │
       ▼
     END

Cada nodo está instrumentado con trace_node() para emitir spans OTel
y trace events al frontend vía SSE.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from app.agents.state import GlobalState
from app.agents.micro_agents.ficha_injector import ficha_injector_node, init_engine_once
from app.agents.micro_agents.guardrail_slm import guardrail_slm_node
from app.agents.micro_agents.profiler_slm import profiler_slm_node
from app.agents.micro_agents.summarizer_slm import summarizer_slm_node
from app.agents.teams.research.agents import (
    plan_research, gather_context, draft_research_response,
)
from app.agents.teams.tool_ops.agents import tool_ops_node
from app.observability.tracer import trace_node

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Explanation functions for trace panel
# ---------------------------------------------------------------------------
def _explain_guardrail(state: Dict[str, Any]) -> str:
    g = state.get("guardrail") or {}
    if g.get("blocked"):
        return f"Bloqueado: {g.get('reason', 'política de seguridad')}"
    return "Aprobado: no se detectaron amenazas"


def _explain_profiler(state: Dict[str, Any]) -> str:
    profile = state.get("profile") or {}
    intent = profile.get("intent", "desconocido")
    ficha = state.get("ficha_cliente") or {}
    seg = ((ficha.get("segmentos") or {}).get("conductual") or {}).get("name", "?")
    return f"Intent: {intent} | Segmento: {seg}"


def _explain_router(state: Dict[str, Any]) -> str:
    profile = state.get("profile") or {}
    intent = (profile.get("intent") or "").lower()
    op_intents = {"saldo", "transferencia", "consulta_movimientos", "bloqueo_tarjeta", "pago"}
    if any(k in intent for k in op_intents):
        return f"Router → ToolOps porque intent='{intent}' es operativo"
    return f"Router → Research porque intent='{intent}' no es operativo"


def _explain_ficha(state: Dict[str, Any]) -> str:
    ficha = state.get("ficha_cliente")
    if ficha:
        uid = ficha.get("user_id", "")
        ver = ficha.get("version", "")
        return f"Ficha cargada: {uid} (v={ver})"
    return "Ficha no disponible — usando defaults"


# ---------------------------------------------------------------------------
# Wrapped nodes with tracing
# ---------------------------------------------------------------------------
traced_ficha_injector = trace_node("ficha_injector", _explain_ficha)(ficha_injector_node)
traced_guardrail = trace_node("guardrail", _explain_guardrail)(guardrail_slm_node)
traced_profiler = trace_node("profiler", _explain_profiler)(profiler_slm_node)
traced_plan_research = trace_node("plan_research")(plan_research)
traced_gather_context = trace_node("gather_context")(gather_context)
traced_draft_response = trace_node("draft_response")(draft_research_response)
traced_tool_ops = trace_node("tool_ops")(tool_ops_node)
traced_summarizer = trace_node("summarizer")(summarizer_slm_node)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
def _route_after_guardrail(state: GlobalState) -> str:
    g = state.get("guardrail") or {}
    if g.get("blocked"):
        return "summarizer"
    return "profiler"


def _route_after_profiler(state: GlobalState) -> str:
    profile = state.get("profile") or {}
    intent = (profile.get("intent") or "").lower()
    # Todas las operaciones bancarias que van a tool_ops
    op_intents = {
        # balance
        "saldo", "balance", "cuanto tengo", "dinero disponible",
        # transferencias
        "transferencia", "transferir", "enviar dinero", "enviar",
        # pagos
        "pago", "pagar", "domiciliacion",
        # movimientos
        "movimiento", "consulta_movimientos", "historial", "ultimos gastos",
        "ultimas compras", "extracto", "estado de cuenta",
        # seguridad
        "bloqueo_tarjeta", "bloqueo", "cancelar tarjeta", "reportar",
        # verificacion de identidad (flujo demo para actividad_atipica)
        "verificar", "verificacion", "verificación", "confirmar identidad",
        "autenticar", "soy yo", "confirmo",
        # productos específicos
        "cashback", "puntos", "recompensa",
        "inversion", "inversiones", "rendimiento", "portafolio", "fondo",
        "ahorro", "ahorros", "meta de ahorro",
        "limite", "cupo", "credito disponible",
        "nomina", "nómina", "pagar empleados",
    }
    if any(k in intent for k in op_intents):
        return "tool_ops"
    return "research"


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build_graph():
    """Compila el StateGraph LangGraph."""
    init_engine_once()  # warmup de modelos al arranque

    g = StateGraph(GlobalState)

    g.add_node("ficha_injector", traced_ficha_injector)
    g.add_node("guardrail", traced_guardrail)
    g.add_node("profiler", traced_profiler)
    g.add_node("plan_research", traced_plan_research)
    g.add_node("gather_context", traced_gather_context)
    g.add_node("draft_response", traced_draft_response)
    g.add_node("tool_ops", traced_tool_ops)
    g.add_node("summarizer", traced_summarizer)

    g.add_edge(START, "ficha_injector")
    g.add_edge("ficha_injector", "guardrail")
    g.add_conditional_edges("guardrail", _route_after_guardrail, {
        "profiler": "profiler",
        "summarizer": "summarizer",
    })
    g.add_conditional_edges("profiler", _route_after_profiler, {
        "research": "plan_research",
        "tool_ops": "tool_ops",
    })
    g.add_edge("plan_research", "gather_context")
    g.add_edge("gather_context", "draft_response")
    g.add_edge("draft_response", "summarizer")
    g.add_edge("tool_ops", "summarizer")
    g.add_edge("summarizer", END)

    compiled = g.compile()
    logger.info("Supervisor LangGraph compilado con tracing OTel")
    return compiled
