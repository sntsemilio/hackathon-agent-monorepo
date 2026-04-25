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

logger = logging.getLogger(__name__)


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
    # Operaciones que requieren tool_ops (saldo, transferencia, etc.)
    op_intents = {"saldo", "transferencia", "consulta_movimientos",
                  "bloqueo_tarjeta", "pago"}
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

    g.add_node("ficha_injector", ficha_injector_node)
    g.add_node("guardrail", guardrail_slm_node)
    g.add_node("profiler", profiler_slm_node)
    g.add_node("plan_research", plan_research)
    g.add_node("gather_context", gather_context)
    g.add_node("draft_response", draft_research_response)
    g.add_node("tool_ops", tool_ops_node)
    g.add_node("summarizer", summarizer_slm_node)

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
    logger.info("Supervisor LangGraph compilado")
    return compiled
