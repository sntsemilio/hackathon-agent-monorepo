"""
backend/mcp_servers/hey_cuentas.py
===================================

MCP Server: hey-cuentas
Tools de lectura sobre cuentas bancarias simuladas.
"""
from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta
from typing import Any, Dict

TOOLS = [
    {
        "name": "consultar_saldo",
        "description": "Consulta el saldo actual de un producto bancario (cuenta de débito, crédito, inversión).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "producto_id": {"type": "string", "description": "ID del producto bancario"}
            },
            "required": ["producto_id"],
        },
    },
    {
        "name": "listar_movimientos",
        "description": "Lista los últimos movimientos de un producto bancario.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "producto_id": {"type": "string", "description": "ID del producto"},
                "desde": {"type": "string", "description": "Fecha inicio YYYY-MM-DD"},
                "hasta": {"type": "string", "description": "Fecha fin YYYY-MM-DD"},
                "limit": {"type": "integer", "description": "Máximo de movimientos"},
            },
            "required": ["producto_id"],
        },
    },
    {
        "name": "obtener_estado_cuenta",
        "description": "Obtiene el resumen del estado de cuenta de un mes específico.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "producto_id": {"type": "string", "description": "ID del producto"},
                "mes": {"type": "string", "description": "Mes en formato YYYY-MM"},
            },
            "required": ["producto_id"],
        },
    },
]

# Movimientos sintéticos
MOCK_MOVIMIENTOS = [
    ("Spotify Premium", -115.00, "entretenimiento"),
    ("OXXO Insurgentes", -89.50, "tienda_conveniencia"),
    ("Transferencia recibida", 3500.00, "transferencia"),
    ("Uber Eats", -245.00, "comida_delivery"),
    ("Nómina Empresa SA", 18500.00, "nomina"),
    ("Amazon MX", -1299.00, "compras_online"),
    ("CFE Recibo", -456.00, "servicios"),
    ("Telmex", -599.00, "servicios"),
    ("Restaurante La Capital", -380.00, "restaurante"),
    ("Gasolinera BP", -850.00, "gasolina"),
    ("Netflix", -199.00, "entretenimiento"),
    ("Mercado Libre", -2150.00, "compras_online"),
    ("Farmacia San Pablo", -320.00, "salud"),
    ("Pago tarjeta crédito", -5000.00, "pago_tc"),
    ("CoDi recibido", 150.00, "codi"),
]


def _seed_from(seed_str: str) -> random.Random:
    h = hashlib.sha256(seed_str.encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def _mock_saldo(producto_id: str) -> float:
    rng = _seed_from(producto_id)
    return round(rng.uniform(1000, 85000), 2)


def _mock_movimientos(producto_id: str, limit: int = 10) -> list[Dict[str, Any]]:
    rng = _seed_from(producto_id)
    count = min(limit, len(MOCK_MOVIMIENTOS))
    selected = rng.sample(MOCK_MOVIMIENTOS, count)
    result = []
    base_date = datetime.now()
    for i, (desc, amount, cat) in enumerate(selected):
        # Vary amounts slightly
        varied = round(amount * rng.uniform(0.8, 1.2), 2)
        date = (base_date - timedelta(days=i + 1)).strftime("%Y-%m-%d")
        result.append({
            "fecha": date,
            "descripcion": desc,
            "monto": varied,
            "categoria": cat,
            "tipo": "abono" if varied > 0 else "cargo",
        })
    return result


async def handle(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    producto_id = args.get("producto_id", "PROD-DEFAULT")

    if tool_name == "consultar_saldo":
        saldo = _mock_saldo(producto_id)
        return {
            "producto_id": producto_id,
            "saldo_actual": saldo,
            "saldo_disponible": round(saldo * 0.95, 2),
            "moneda": "MXN",
            "fecha_corte": datetime.now().strftime("%Y-%m-%d"),
        }

    if tool_name == "listar_movimientos":
        limit = args.get("limit", 10)
        movs = _mock_movimientos(producto_id, limit)
        return {
            "producto_id": producto_id,
            "movimientos": movs,
            "total": len(movs),
        }

    if tool_name == "obtener_estado_cuenta":
        saldo = _mock_saldo(producto_id)
        mes = args.get("mes", datetime.now().strftime("%Y-%m"))
        return {
            "producto_id": producto_id,
            "mes": mes,
            "saldo_inicial": round(saldo * 0.85, 2),
            "total_abonos": round(saldo * 0.6, 2),
            "total_cargos": round(saldo * 0.45, 2),
            "saldo_final": saldo,
            "num_movimientos": 28,
        }

    return {"error": f"Tool {tool_name} not found in hey_cuentas"}
