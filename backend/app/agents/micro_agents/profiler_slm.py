"""
backend/app/agents/micro_agents/profiler_slm.py
================================================

Profiler conversacional. Combina dos perfiles:

    1) Perfil ESTÁTICO (ficha_cliente):
       quién ES el usuario según los 3 modelos de clustering offline
       (conductual / transaccional / salud_financiera).

    2) Perfil DINÁMICO (mensaje actual):
       cómo está HABLANDO ahora (intención, sentimiento, urgencia,
       formalidad, tema).

El nodo emite un `ConversationalProfile` que el supervisor y los teams
de Research / ToolOps usan para personalizar la respuesta final.

CAMBIO PRINCIPAL (BLOQUEADOR 2 del documento de contexto):
    Antes: el prompt sólo tomaba el texto del usuario.
    Ahora: lee `state["ficha_cliente"]` y enriquece el system prompt
    con los 3 segmentos para que el LLM tenga el contexto completo.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.core.llm import get_llm  # ajusta si tu helper LiteLLM se llama distinto

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output schema del profiler
# ---------------------------------------------------------------------------
class ConversationalProfile(BaseModel):
    """Perfil que combina lo estático (ficha) con lo dinámico (mensaje)."""

    # Dinámico: qué está pasando AHORA
    intent: str = Field(..., description="intención principal del mensaje")
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    urgency: Literal["low", "medium", "high"] = "low"
    formality: Literal["casual", "neutral", "formal"] = "neutral"
    topic: Optional[str] = Field(default=None, description="tema central")
    mentions_money_amount: bool = False

    # Estático: quién ES el usuario (copiado de la ficha para que viaje
    # con el state hacia los teams downstream)
    behavioral_segment: Optional[str] = None
    transactional_segment: Optional[str] = None
    financial_health_segment: Optional[str] = None
    top_spending_categories: List[str] = Field(default_factory=list)
    offer_strategy: Optional[str] = None
    candidate_suggestions: List[str] = Field(default_factory=list)

    # Hint que el supervisor/research pueden usar como atajo
    persona_key: Optional[str] = Field(
        default=None,
        description="Clave del system prompt en SYSTEM_PROMPTS_BY_SEGMENT (research/agents.py)",
    )


# ---------------------------------------------------------------------------
# Plantillas de prompt
# ---------------------------------------------------------------------------
_PROFILER_SYSTEM = """\
Eres el módulo Profiler del agente Havi (Hey Banco).
Tu trabajo es producir un perfil conversacional combinando:
  (a) lo que YA sabemos del usuario (ficha de cliente, abajo) y
  (b) lo que dice el usuario en este turno.

Devuelve SIEMPRE un JSON válido con exactamente este schema:
{
  "intent": "string",
  "sentiment": "positive|neutral|negative",
  "urgency": "low|medium|high",
  "formality": "casual|neutral|formal",
  "topic": "string|null",
  "mentions_money_amount": true|false
}

No agregues comentarios, sólo el JSON.
"""

_FICHA_BLOCK_TEMPLATE = """\
=== Ficha del cliente (estático, no inventes datos fuera de aquí) ===
- Segmento conductual: {behavioral}
- Segmento transaccional: {transactional}
  · top categorías de gasto: {top_categories}
- Salud financiera: {financial}
  · estrategia de oferta sugerida: {offer_strategy}
- Sugerencias candidatas (sólo introducir si es orgánico al tema):
  {suggestions}
================================================================
"""

_NO_FICHA_BLOCK = (
    "=== Ficha del cliente: NO DISPONIBLE (usuario nuevo o ficha no indexada).\n"
    "    Trata el mensaje sin asumir segmento; el resto del pipeline degradará a default. ===\n"
)


def _render_ficha_block(ficha: Optional[Dict[str, Any]]) -> str:
    if not ficha:
        return _NO_FICHA_BLOCK
    seg = ficha.get("segmentos", {}) or {}
    cond = seg.get("conductual", {}) or {}
    trans = seg.get("transaccional", {}) or {}
    salud = seg.get("salud_financiera", {}) or {}
    return _FICHA_BLOCK_TEMPLATE.format(
        behavioral=cond.get("name") or "desconocido",
        transactional=trans.get("name") or "desconocido",
        top_categories=", ".join(trans.get("top_spending_categories") or []) or "—",
        financial=salud.get("name") or "desconocido",
        offer_strategy=salud.get("offer_strategy") or "—",
        suggestions=", ".join(ficha.get("sugerencias_candidatas") or []) or "—",
    )


def _build_user_prompt(user_text: str, ficha_block: str) -> str:
    return (
        f"{ficha_block}\n"
        f"=== Mensaje del usuario en este turno ===\n"
        f"{user_text}\n"
        f"=== Fin del mensaje ===\n\n"
        f"Devuelve únicamente el JSON descrito en las instrucciones del sistema."
    )


# ---------------------------------------------------------------------------
# Nodo LangGraph
# ---------------------------------------------------------------------------
async def profiler_slm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo del supervisor. Lee:
        - state["input_text"]      mensaje actual del usuario
        - state["ficha_cliente"]   ficha precalculada (FichaInjector)

    Emite:
        - state["profile"]         ConversationalProfile.model_dump()
    """
    user_text: str = state.get("input_text") or ""
    ficha: Optional[Dict[str, Any]] = state.get("ficha_cliente")

    ficha_block = _render_ficha_block(ficha)
    user_prompt = _build_user_prompt(user_text, ficha_block)

    llm = get_llm(role="profiler")  # típicamente un SLM rápido (Haiku, Llama 8B, etc.)
    raw = await llm.acomplete(
        system=_PROFILER_SYSTEM,
        user=user_prompt,
        temperature=0.0,
        max_tokens=300,
        response_format={"type": "json_object"},
    )

    dynamic = _safe_parse_json(raw, fallback={
        "intent": "informacion_general",
        "sentiment": "neutral",
        "urgency": "low",
        "formality": "neutral",
        "topic": None,
        "mentions_money_amount": False,
    })

    profile = _merge_profile(dynamic=dynamic, ficha=ficha)
    logger.info(
        "Profiler: intent=%s sentiment=%s persona_key=%s",
        profile.intent, profile.sentiment, profile.persona_key,
    )

    return {"profile": profile.model_dump()}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_parse_json(raw: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON robusto: tolera fences ```json y texto antes/después."""
    if not raw:
        return fallback
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Último intento: buscar el primer bloque {...}
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            try:
                return json.loads(text[first:last + 1])
            except json.JSONDecodeError:
                pass
        logger.warning("Profiler returned non-JSON output, using fallback. Raw=%r", raw[:200])
        return fallback


def _merge_profile(
    dynamic: Dict[str, Any],
    ficha: Optional[Dict[str, Any]],
) -> ConversationalProfile:
    """Une lo dinámico (LLM) con lo estático (ficha)."""
    seg = (ficha or {}).get("segmentos", {}) or {}
    cond = seg.get("conductual", {}) or {}
    trans = seg.get("transaccional", {}) or {}
    salud = seg.get("salud_financiera", {}) or {}

    return ConversationalProfile(
        intent=str(dynamic.get("intent", "informacion_general"))[:120],
        sentiment=_clip(dynamic.get("sentiment"), {"positive", "neutral", "negative"}, "neutral"),
        urgency=_clip(dynamic.get("urgency"), {"low", "medium", "high"}, "low"),
        formality=_clip(dynamic.get("formality"), {"casual", "neutral", "formal"}, "neutral"),
        topic=(dynamic.get("topic") or None),
        mentions_money_amount=bool(dynamic.get("mentions_money_amount", False)),

        behavioral_segment=cond.get("name"),
        transactional_segment=trans.get("name"),
        financial_health_segment=salud.get("name"),
        top_spending_categories=list(trans.get("top_spending_categories") or []),
        offer_strategy=salud.get("offer_strategy"),
        candidate_suggestions=list((ficha or {}).get("sugerencias_candidatas") or []),

        persona_key=cond.get("name"),
    )


def _clip(value: Any, allowed: set, default: str) -> str:
    return value if value in allowed else default
