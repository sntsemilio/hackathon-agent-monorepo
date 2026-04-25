"""
backend/app/agents/micro_agents/summarizer_slm.py
==================================================

Último nodo. Toma el `draft_response` (de research o tool_ops) y produce
la respuesta final para el usuario, con:
  - tono ya fijado por el segmento conductual (lo trae draft_response)
  - inyección final de la sugerencia candidata si aplica y no se introdujo
    aún en el draft
  - tarjeta accionable opcional cuando hay un product hint

El supervisor lo expone como nodo terminal (`-> END`).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _build_action_card(suggestion: Optional[str]) -> Optional[Dict[str, Any]]:
    """Devuelve una tarjeta accionable canónica si la sugerencia mapea a un deep link."""
    if not suggestion:
        return None
    deep_link_map = {
        "hey_pro": ("Activa Hey Pro", "Hasta 1% de cashback en compras.", "/pro"),
        "cashback_hey_pro": ("Hey Pro · Cashback", "Activa el plan y empieza a recuperar dinero.", "/pro/cashback"),
        "inversion_hey": ("Inversión Hey", "Pon tu dinero a generar GAT.", "/inversion"),
        "tarjeta_credito_hey": ("Tarjeta Hey", "Construye historial sin anualidad.", "/credito/hey"),
        "tarjeta_credito_garantizada": ("Tarjeta garantizada", "Empieza a construir crédito.", "/credito/garantizada"),
        "seguro_vida": ("Seguro de vida", "Protege a quien más quieres.", "/seguros/vida"),
        "seguro_viaje": ("Seguro de viaje", "Cobertura internacional al instante.", "/seguros/viaje"),
        "cuenta_negocios": ("Cuenta de negocios", "Maneja tu PYME desde la app.", "/negocios"),
        "credito_pyme": ("Crédito PYME", "Capital para crecer.", "/credito/pyme"),
        "tarjeta_credito_negocios": ("Tarjeta negocios", "Crédito para tu operación.", "/credito/negocios"),
        "ahorro_programado": ("Ahorro programado", "Aparta y crece automáticamente.", "/ahorro"),
        "plan_pago_reestructura": ("Plan de pagos", "Te ayudamos a reestructurar.", "/soporte/reestructura"),
        "asesoria_financiera": ("Asesoría 1:1", "Habla con un experto.", "/asesoria"),
        "verificacion_identidad": ("Verificar identidad", "Confirma tu identidad para continuar.", "/verificacion"),
        "primer_ahorro": ("Tu primer ahorro", "Empieza con $100.", "/ahorro/primer"),
        "onboarding_premium": ("Conoce Hey", "Tour de funciones esenciales.", "/onboarding"),
        "codi": ("CoDi", "Cobra y paga sin comisiones.", "/codi"),
    }
    if suggestion not in deep_link_map:
        return None
    title, desc, deep_link = deep_link_map[suggestion]
    return {
        "type": "action_card",
        "id": suggestion,
        "title": title,
        "description": desc,
        "deep_link": deep_link,
    }


async def summarizer_slm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Toma el draft y arma la respuesta final + componentes UI opcionales.
    """
    draft = (state.get("draft_response") or "").strip()
    draft_meta = state.get("draft_meta") or {}
    guardrail = state.get("guardrail") or {}
    profile = state.get("profile") or {}
    ficha = state.get("ficha_cliente") or {}

    # Si el guardrail bloqueó, ya hay un canned response listo
    if guardrail.get("blocked"):
        return {
            "final_response": draft or
                              "No puedo ayudarte con eso. ¿En qué más te puedo apoyar?",
            "ui_components": [],
        }

    # Step-up auth: anteponer aviso
    final = draft
    if guardrail.get("requires_step_up_auth"):
        final = ("Antes de continuar necesito verificar tu identidad. "
                 "Te envié un código a tu app.\n\n" + final)

    # Tarjeta accionable
    components: List[Dict[str, Any]] = []
    suggestion_offered = draft_meta.get("suggestion_offered")
    if suggestion_offered and not _draft_already_mentions(final, suggestion_offered):
        card = _build_action_card(suggestion_offered)
        if card:
            components.append(card)

    logger.info("summarizer: persona=%s components=%d",
                ((ficha.get("segmentos") or {}).get("conductual") or {}).get("name"),
                len(components))
    return {
        "final_response": final or "Estoy aquí para ayudarte. ¿Puedes decirme un poco más?",
        "ui_components": components,
    }


def _draft_already_mentions(text: str, suggestion: str) -> bool:
    if not text or not suggestion:
        return False
    needle = suggestion.replace("_", " ").lower()
    return needle in text.lower()
