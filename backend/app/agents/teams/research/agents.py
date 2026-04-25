"""
backend/app/agents/teams/research/agents.py
============================================

Team de Research del agente Havi (Hey Banco).

Nodos LangGraph:
    - plan_research          : decide qué buscar y con qué profundidad
    - gather_context         : pulls del vector store (RedisVL HNSW)
    - draft_research_response: redacta la respuesta final con personalización

CAMBIOS PRINCIPALES (FALTANTES 3 y 4 del documento de contexto):
    - Ambos nodos leen `state["ficha_cliente"]` y construyen un bloque
      de personalización que se inyecta al system prompt del LLM.
    - El system prompt cambia según el segmento conductual.
    - `draft_research_response` decide si introducir orgánicamente una
      sugerencia de `ficha_cliente.sugerencias_candidatas` cuando el
      tema lo permite.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.llm import get_llm
from app.rag.vector_store import VectorStore  # ajusta si tu helper se llama distinto

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompts por segmento conductual (Modelo 1, K=7)
# ---------------------------------------------------------------------------
SYSTEM_PROMPTS_BY_SEGMENT: Dict[str, str] = {
    "usuario_basico_bajo_enganche": (
        "Eres Havi, asistente de Hey Banco. El usuario está comenzando su vida "
        "financiera. Usa lenguaje simple, evita jerga. Explica conceptos básicos. "
        "Detecta señales de churn y ofrece beneficios de retención proactivamente. "
        "Prioriza: ahorro, primer crédito, educación financiera."
    ),
    "profesional_prospero_inversor": (
        "Eres Havi, asesor financiero premium de Hey Banco. Usuario de alto perfil "
        "con inversiones activas. Lenguaje sofisticado y técnico. Menciona "
        "proactivamente oportunidades de inversión, GAT real, beneficios fiscales. "
        "Tono ejecutivo."
    ),
    "usuario_estres_financiero": (
        "Eres Havi, asistente empático de Hey Banco. El usuario puede estar bajo "
        "presión financiera (utilización de crédito alta). Evita generar ansiedad. "
        "Ofrece soluciones concretas: reestructuración, planes de pago. "
        "Tono cálido y comprensivo."
    ),
    "joven_digital_hey_pro": (
        "Eres Havi de Hey Banco. Usuario joven y tecnológico con Hey Pro activo. "
        "Lenguaje casual, referencias digitales. Aprovecha que usa mucho la app. "
        "Prioriza: cashback, Hey Shop, CoDi. Tono amigable y rápido."
    ),
    "actividad_atipica_alerta": (
        "MODO RESTRINGIDO. Responde ÚNICAMENTE consultas básicas de saldo e "
        "información general. Para cualquier operación solicita verificación de "
        "identidad primero. NO ejecutes cambios ni transferencias sin validación."
    ),
    "empresario_alto_volumen": (
        "Eres Havi, asesor de negocios de Hey Banco. Empresario con alto volumen "
        "de operaciones. Prioriza: cuenta negocios, nómina empresarial, crédito "
        "PYME, facturación. Tono profesional orientado a resultados."
    ),
    "cliente_promedio_estable": (
        "Eres Havi de Hey Banco. Cliente satisfecho y estable. Mantén su "
        "satisfacción. Ofrece mejoras graduales: Hey Pro, seguros, inversiones. "
        "Tono amigable y directo."
    ),
}

DEFAULT_SYSTEM_PROMPT = (
    "Eres Havi, asistente de Hey Banco. Responde con precisión, calidez y "
    "claridad. Cuando no tengas certeza, sé honesto y ofrece pasos siguientes."
)


# Mapas auxiliares: salud financiera y transaccional refinan la personalización
SAFETY_RAILS_BY_FINANCIAL_HEALTH: Dict[str, str] = {
    "presion_financiera": (
        "ATENCIÓN: el usuario muestra presión financiera. NO ofrezcas productos "
        "que aumenten endeudamiento (tarjetas adicionales, créditos no esenciales). "
        "Prioriza alivio, planes de pago y educación."
    ),
    "en_construccion_crediticia": (
        "El usuario está construyendo historial. Productos válidos: tarjetas de "
        "crédito básicas, esquemas con cashback, ahorro programado."
    ),
    "activo_saludable": (
        "El usuario tiene salud financiera activa. Puedes proponer productos de "
        "inversión, seguros y mejoras de portafolio."
    ),
    "solido_sin_credito": (
        "El usuario es sólido y sin uso de crédito. Buen candidato a primera "
        "tarjeta premium o productos de inversión."
    ),
}


# ---------------------------------------------------------------------------
# Helpers de personalización
# ---------------------------------------------------------------------------
def _ficha_segments(ficha: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    seg = (ficha or {}).get("segmentos", {}) or {}
    return {
        "behavioral": (seg.get("conductual") or {}),
        "transactional": (seg.get("transaccional") or {}),
        "financial_health": (seg.get("salud_financiera") or {}),
    }


def _pick_persona_prompt(ficha: Optional[Dict[str, Any]]) -> str:
    """Elige el system prompt base según el segmento conductual."""
    if not ficha:
        return DEFAULT_SYSTEM_PROMPT
    name = ((ficha.get("segmentos") or {}).get("conductual") or {}).get("name")
    return SYSTEM_PROMPTS_BY_SEGMENT.get(name or "", DEFAULT_SYSTEM_PROMPT)


def _personalization_block(ficha: Optional[Dict[str, Any]]) -> str:
    """
    Construye el bloque de contexto que se inyecta al LLM debajo del system prompt.
    Este bloque viaja con CADA llamada (plan + draft) para que el LLM no pierda
    contexto.
    """
    if not ficha:
        return (
            "[PERSONALIZACIÓN]\n"
            "  Ficha: NO DISPONIBLE.\n"
            "  Comportamiento: trata al usuario como cliente_promedio_estable.\n"
            "  No inventes segmentos ni datos del usuario.\n"
        )

    s = _ficha_segments(ficha)
    cond = s["behavioral"]
    trans = s["transactional"]
    salud = s["financial_health"]
    suggestions = ficha.get("sugerencias_candidatas") or []

    rails = SAFETY_RAILS_BY_FINANCIAL_HEALTH.get(salud.get("name") or "", "")

    lines = [
        "[PERSONALIZACIÓN]",
        f"  Segmento conductual:    {cond.get('name', 'desconocido')}",
        f"  Segmento transaccional: {trans.get('name', 'desconocido')}",
        f"    · top categorías: {', '.join(trans.get('top_spending_categories') or []) or '—'}",
        f"  Salud financiera:       {salud.get('name', 'desconocido')}",
        f"    · estrategia de oferta: {salud.get('offer_strategy') or '—'}",
        f"  Sugerencias candidatas: {', '.join(suggestions) or '—'}",
        "",
        "Reglas:",
        "  1. Adapta tono y vocabulario al segmento conductual.",
        "  2. Si introduces una sugerencia candidata, hazlo SOLO cuando sea orgánico al "
        "tema y nunca más de UNA por turno.",
        "  3. Respeta los safety rails por salud financiera (abajo).",
    ]
    if rails:
        lines += ["", f"[SAFETY RAILS] {rails}"]
    return "\n".join(lines)


def _should_offer_suggestion(
    profile: Optional[Dict[str, Any]],
    ficha: Optional[Dict[str, Any]],
) -> Optional[str]:
    """
    Heurística mínima para decidir si proponer una sugerencia candidata.
    Devuelve el nombre de la sugerencia o None.
    El LLM decide la fraseología, esto sólo desbloquea la posibilidad.
    """
    if not ficha or not profile:
        return None

    sentiment = profile.get("sentiment", "neutral")
    urgency = profile.get("urgency", "low")
    intent = (profile.get("intent") or "").lower()

    # No vendas si el usuario está estresado o con urgencia alta
    if sentiment == "negative" or urgency == "high":
        return None

    # Tampoco si la salud financiera lo desaconseja
    salud = ((ficha.get("segmentos") or {}).get("salud_financiera") or {}).get("name")
    if salud == "presion_financiera":
        return None

    # Y nunca durante "intent" puramente operativos (saldo, soporte, queja)
    blocking_intents = {"saldo", "soporte", "queja", "reclamo", "bloqueo", "fraude"}
    if any(b in intent for b in blocking_intents):
        return None

    suggestions: List[str] = ficha.get("sugerencias_candidatas") or []
    return suggestions[0] if suggestions else None


# ---------------------------------------------------------------------------
# Nodo: plan_research
# ---------------------------------------------------------------------------
async def plan_research(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide qué información hace falta buscar para responder al usuario.
    La salida es un dict con `queries: list[str]` y `depth: 'shallow'|'deep'`.
    """
    ficha = state.get("ficha_cliente")
    profile = state.get("profile") or {}
    user_text = state.get("input_text") or ""

    persona_prompt = _pick_persona_prompt(ficha)
    personalization = _personalization_block(ficha)

    system = (
        f"{persona_prompt}\n\n"
        f"{personalization}\n\n"
        "Tarea: a partir del mensaje del usuario, propón hasta 3 consultas de "
        "búsqueda concisas que extraigan el contexto necesario para responder "
        "con precisión. Devuelve JSON: "
        '{"queries": ["..."], "depth": "shallow|deep"}.'
    )

    llm = get_llm(role="planner")
    raw = await llm.acomplete(
        system=system,
        user=f"Mensaje del usuario:\n{user_text}\n\nIntent detectado: {profile.get('intent')}",
        temperature=0.2,
        max_tokens=300,
        response_format={"type": "json_object"},
    )

    plan = _safe_parse_plan(raw)
    logger.info("plan_research: %d queries depth=%s", len(plan["queries"]), plan["depth"])
    return {"research_plan": plan}


# ---------------------------------------------------------------------------
# Nodo: gather_context
# ---------------------------------------------------------------------------
async def gather_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recupera contexto del vector store usando las queries del plan.
    """
    plan = state.get("research_plan") or {"queries": [state.get("input_text", "")]}
    queries: List[str] = plan.get("queries") or [state.get("input_text", "")]

    store = VectorStore()
    contexts: List[Dict[str, Any]] = []
    for q in queries[:3]:
        if not q:
            continue
        hits = await store.hybrid_search(q, top_k=5)
        contexts.append({"query": q, "hits": hits})

    logger.info("gather_context: %d queries, %d total hits",
                len(contexts), sum(len(c.get("hits") or []) for c in contexts))
    return {"research_context": contexts}


# ---------------------------------------------------------------------------
# Nodo: draft_research_response
# ---------------------------------------------------------------------------
async def draft_research_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redacta la respuesta final personalizada.
    Inyecta system prompt por segmento, safety rails y, si procede,
    sugiere orgánicamente uno de los productos candidatos.
    """
    ficha = state.get("ficha_cliente")
    profile = state.get("profile") or {}
    contexts = state.get("research_context") or []
    user_text = state.get("input_text") or ""

    persona_prompt = _pick_persona_prompt(ficha)
    personalization = _personalization_block(ficha)
    suggestion_to_offer = _should_offer_suggestion(profile, ficha)

    suggestion_clause = ""
    if suggestion_to_offer:
        suggestion_clause = (
            f"\n[SUGERENCIA PERMITIDA EN ESTE TURNO]\n"
            f"  Si el tema lo permite y de forma natural, puedes mencionar "
            f"`{suggestion_to_offer}` UNA sola vez. No fuerces la venta. "
            f"Si no encaja, no la menciones.\n"
        )

    system = (
        f"{persona_prompt}\n\n"
        f"{personalization}"
        f"{suggestion_clause}\n"
        "Reglas adicionales:\n"
        "  - Si no tienes información, dilo claramente y propón siguiente paso.\n"
        "  - Cita los datos específicos del usuario sólo si vienen en la ficha.\n"
        "  - Tu respuesta debe ser breve y accionable (máx 4-6 oraciones).\n"
    )

    user_block = (
        f"Mensaje del usuario:\n{user_text}\n\n"
        f"Contexto recuperado (RAG):\n{_format_contexts(contexts)}\n\n"
        f"Perfil dinámico: intent={profile.get('intent')}, "
        f"sentiment={profile.get('sentiment')}, urgency={profile.get('urgency')}.\n\n"
        "Redacta la respuesta final para el usuario."
    )

    llm = get_llm(role="responder")
    response_text = await llm.acomplete(
        system=system,
        user=user_block,
        temperature=0.4,
        max_tokens=500,
    )

    logger.info(
        "draft_response: persona=%s suggestion_offered=%s",
        ((ficha or {}).get("segmentos", {}) or {}).get("conductual", {}).get("name"),
        bool(suggestion_to_offer),
    )

    return {
        "draft_response": (response_text or "").strip(),
        "draft_meta": {
            "persona_key": ((ficha or {}).get("segmentos", {}) or {}).get("conductual", {}).get("name"),
            "suggestion_offered": suggestion_to_offer,
        },
    }


# ---------------------------------------------------------------------------
# Helpers locales
# ---------------------------------------------------------------------------
def _safe_parse_plan(raw: str) -> Dict[str, Any]:
    import json
    fallback = {"queries": [], "depth": "shallow"}
    if not raw:
        return fallback
    text = raw.strip().strip("`")
    if text.lower().startswith("json"):
        text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        first, last = text.find("{"), text.rfind("}")
        if first == -1 or last == -1:
            return fallback
        try:
            data = json.loads(text[first:last + 1])
        except json.JSONDecodeError:
            return fallback

    queries = [q for q in (data.get("queries") or []) if isinstance(q, str)]
    depth = data.get("depth") if data.get("depth") in {"shallow", "deep"} else "shallow"
    return {"queries": queries[:3], "depth": depth}


def _format_contexts(contexts: List[Dict[str, Any]]) -> str:
    if not contexts:
        return "(sin resultados)"
    blocks = []
    for c in contexts:
        hits = c.get("hits") or []
        snippets = [
            f"  - {h.get('text') or h.get('content') or ''}"[:300]
            for h in hits[:3]
        ]
        blocks.append(f"Q: {c.get('query')}\n" + ("\n".join(snippets) or "  (sin hits)"))
    return "\n\n".join(blocks)
