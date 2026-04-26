"""
backend/mcp_servers/hey_credito.py
====================================

MCP Server: hey-credito
Tools de crédito y tarjetas.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any, Dict

TOOLS = [
    {
        "name": "consultar_limite",
        "description": "Consulta el límite de crédito y saldo disponible de una tarjeta.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tarjeta_id": {"type": "string", "description": "ID de la tarjeta de crédito"},
            },
            "required": ["tarjeta_id"],
        },
    },
    {
        "name": "pagar_tarjeta",
        "description": "Realiza un pago a tarjeta de crédito. OPERACIÓN MUTANTE: requiere confirmación.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tarjeta_id": {"type": "string", "description": "ID de la tarjeta"},
                "monto": {"type": "number", "description": "Monto a pagar en MXN"},
                "fuente": {"type": "string", "description": "Cuenta origen del pago"},
            },
            "required": ["tarjeta_id", "monto"],
        },
    },
    {
        "name": "convertir_a_msi",
        "description": "Convierte una compra a meses sin intereses. OPERACIÓN MUTANTE.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transaccion_id": {"type": "string", "description": "ID de la transacción"},
                "plazo": {"type": "integer", "description": "Número de meses (3, 6, 12, 18)"},
            },
            "required": ["transaccion_id", "plazo"],
        },
    },
    {
        "name": "solicitar_aumento_linea",
        "description": "Solicita un aumento de línea de crédito. OPERACIÓN MUTANTE. BLOQUEADA si salud=presion_financiera.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tarjeta_id": {"type": "string", "description": "ID de la tarjeta"},
                "monto": {"type": "number", "description": "Monto solicitado de aumento"},
            },
            "required": ["tarjeta_id", "monto"],
        },
    },
]


def _seed(s: str) -> random.Random:
    return random.Random(int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big"))


async def handle(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "consultar_limite":
        tarjeta_id = args.get("tarjeta_id", "TC-DEFAULT")
        rng = _seed(tarjeta_id)
        limite = round(rng.uniform(10000, 120000), 2)
        usado = round(limite * rng.uniform(0.1, 0.7), 2)
        return {
            "tarjeta_id": tarjeta_id,
            "limite_credito": limite,
            "saldo_usado": usado,
            "disponible": round(limite - usado, 2),
            "fecha_corte": "2026-05-15",
            "fecha_pago": "2026-05-25",
            "pago_minimo": round(usado * 0.05, 2),
            "pago_no_intereses": usado,
        }

    if tool_name == "pagar_tarjeta":
        monto = args.get("monto", 0)
        return {
            "status": "ejecutado",
            "tarjeta_id": args.get("tarjeta_id", ""),
            "monto_pagado": monto,
            "fuente": args.get("fuente", "cuenta_debito_principal"),
            "referencia": f"PAG-{hashlib.md5(str(monto).encode()).hexdigest()[:8].upper()}",  # noqa: S324
            "mensaje": f"Pago de ${monto:,.2f} MXN aplicado exitosamente.",
        }

    if tool_name == "convertir_a_msi":
        plazo = args.get("plazo", 6)
        return {
            "status": "ejecutado",
            "transaccion_id": args.get("transaccion_id", ""),
            "plazo_meses": plazo,
            "mensaje": f"Compra convertida a {plazo} MSI exitosamente.",
        }

    if tool_name == "solicitar_aumento_linea":
        return {
            "status": "en_revision",
            "tarjeta_id": args.get("tarjeta_id", ""),
            "monto_solicitado": args.get("monto", 0),
            "mensaje": "Tu solicitud de aumento de línea está en revisión. Te notificaremos en 24-48 hrs.",
        }

    return {"error": f"Tool {tool_name} not found in hey_credito"}
