"""
backend/app/agents/teams/tool_ops/agents.py
============================================

Team de operaciones de herramientas (saldo, transferencias simuladas,
movimientos). Para el datathon devolvemos respuestas plausibles basadas
en la ficha; en producción cada tool conectaría con servicios reales.

Diseño: una sola función `tool_ops_node` que internamente despacha por intent.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _format_currency(amount: float) -> str:
    return f"${amount:,.2f} MXN"


async def tool_ops_node(state: Dict[str, Any]) -> Dict[str, Any]:
    profile = state.get("profile") or {}
    intent = (profile.get("intent") or "").lower()
    user_id = state.get("user_id") or ""
    ficha = state.get("ficha_cliente") or {}

    if "saldo" in intent:
        text = (f"Tu saldo disponible en cuenta de débito principal es "
                f"{_format_currency(_mock_saldo(user_id))}.")
        return {"draft_response": text,
                "draft_meta": {"source": "tool_ops", "tool": "consulta_saldo"}}

    if "transferencia" in intent or "pago" in intent:
        text = ("Para realizar la transferencia necesito que confirmes el monto y "
                "la cuenta destino. ¿Quieres que la prepare ahora?")
        return {"draft_response": text,
                "draft_meta": {"source": "tool_ops", "tool": "transferencia",
                               "needs_confirmation": True}}

    if "movimiento" in intent or "consulta_movimientos" in intent:
        text = ("Tus últimos 5 movimientos: 1) Cargo Spotify · 2) Compra OXXO · "
                "3) Transferencia recibida · 4) Compra restaurante · 5) Pago tarjeta. "
                "¿Quieres ver el detalle de alguno?")
        return {"draft_response": text,
                "draft_meta": {"source": "tool_ops", "tool": "consulta_movimientos"}}

    # Fallback: dejar que research lo tome (no debería pasar por el router)
    return {"draft_response": "Déjame revisar esa solicitud.",
            "draft_meta": {"source": "tool_ops", "tool": "fallback"}}


def _mock_saldo(user_id: str) -> float:
    # Determinista por user_id para que el demo sea estable
    import hashlib
    h = hashlib.sha256(user_id.encode()).digest()
    return round(((h[0] << 8) + h[1]) % 50000 + 1000, 2)
