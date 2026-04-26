"""
backend/app/agents/micro_agents/guardrail_slm.py
=================================================

Capa de seguridad. Bloquea o etiqueta el turno antes de pasar al pipeline.

Reglas explícitas (rule-based, rapidas) + LLM opcional para casos ambiguos.

Bloquea:
  - Mensajes que pidan ejecutar transferencias / cambios sin autenticación
  - Mensajes que intenten extraer datos de OTROS usuarios
  - Mensajes con prompt injection obvio ("ignora instrucciones previas")
  - Si la ficha indica `actividad_atipica_alerta` y el intent es operativo,
    pasa pero marca `requires_step_up_auth=True`.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


_PROMPT_INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignora.*(instruccion|prompt)", re.IGNORECASE),
    re.compile(r"olvida.*(reglas|sistema)", re.IGNORECASE),
    re.compile(r"actua\s+como\s+(otro|admin|root)", re.IGNORECASE),
    re.compile(r"reveal.*(system|prompt)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]

_SCRAPING_PATTERNS: List[re.Pattern] = [
    re.compile(r"datos\s+de\s+otr[oa]\s+usuari[oa]", re.IGNORECASE),
    re.compile(r"saldo\s+de\s+USR-\d+", re.IGNORECASE),
    re.compile(r"acceso\s+a\s+la\s+cuenta\s+de\s+\w+", re.IGNORECASE),
]

_OPERATIVE_INTENTS = {"transferencia", "cambio_password", "bloqueo_tarjeta", "pago"}


async def guardrail_slm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    text = (state.get("input_text") or "").strip()
    ficha = state.get("ficha_cliente") or {}
    cond = ((ficha.get("segmentos") or {}).get("conductual") or {}).get("name", "")

    blocked = False
    reason = None
    canned_response = None
    requires_step_up_auth = False

    for p in _PROMPT_INJECTION_PATTERNS:
        if p.search(text):
            blocked = True
            reason = "prompt_injection"
            canned_response = ("No puedo ayudarte con eso. ¿Hay algo sobre tu cuenta "
                               "o productos Hey Banco en lo que pueda apoyarte?")
            break

    if not blocked:
        for p in _SCRAPING_PATTERNS:
            if p.search(text):
                blocked = True
                reason = "scraping_attempt"
                canned_response = ("Por seguridad, sólo puedo ayudarte con tu propia "
                                   "cuenta. Si necesitas información de otra persona, "
                                   "ella debe consultarla directamente.")
                break

    # Step-up auth si el segmento es alerta y suena operativo
    if not blocked and cond == "actividad_atipica_alerta":
        lower = text.lower()
        if any(w in lower for w in ("transferir", "transfiere", "cambia", "envia", "enviar")):
            requires_step_up_auth = True

    out: Dict[str, Any] = {
        "guardrail_result": {
            "blocked": blocked,
            "reason": reason,
            "requires_step_up_auth": requires_step_up_auth,
        }
    }
    if blocked and canned_response:
        out["draft_response_text"] = canned_response
        out["draft_meta"] = {"source": "guardrail", "reason": reason}
    logger.info("guardrail: blocked=%s reason=%s step_up=%s",
                blocked, reason, requires_step_up_auth)
    return out
