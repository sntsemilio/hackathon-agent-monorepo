"""
backend/mcp_servers/hey_pro_shop.py
====================================
MCP Server: hey-pro-shop — Hey Pro, cashback, ofertas.
"""
from __future__ import annotations
import hashlib, random
from typing import Any, Dict

TOOLS = [
    {"name": "consultar_status_pro", "description": "Status de Hey Pro del usuario.",
     "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}},
    {"name": "activar_hey_pro", "description": "Activa Hey Pro. MUTANTE.",
     "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}},
    {"name": "consultar_cashback", "description": "Cashback acumulado.",
     "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "periodo": {"type": "string"}}, "required": ["user_id"]}},
    {"name": "listar_ofertas_personalizadas", "description": "Ofertas personalizadas.",
     "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}},
]

def _seed(s: str) -> random.Random:
    return random.Random(int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big"))

OFERTAS = [
    {"titulo": "2% cashback en Amazon", "vigencia": "2026-05-31", "categoria": "compras_online"},
    {"titulo": "3% cashback en gasolina", "vigencia": "2026-05-15", "categoria": "gasolina"},
    {"titulo": "5% cashback en Uber Eats", "vigencia": "2026-04-30", "categoria": "delivery"},
    {"titulo": "1.5% cashback en todo", "vigencia": "2026-06-30", "categoria": "general"},
    {"titulo": "Doble puntos en viajes", "vigencia": "2026-05-20", "categoria": "viajes"},
]

async def handle(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    uid = args.get("user_id", "USR")
    rng = _seed(uid)
    if tool_name == "consultar_status_pro":
        activo = rng.random() > 0.4
        return {"user_id": uid, "hey_pro_activo": activo,
                "fecha_activacion": "2025-11-01" if activo else None,
                "nivel": "Gold" if activo and rng.random() > 0.5 else "Silver" if activo else None,
                "cashback_acumulado": round(rng.uniform(50, 3000), 2) if activo else 0}
    if tool_name == "activar_hey_pro":
        return {"status": "ejecutado", "user_id": uid,
                "mensaje": "¡Hey Pro activado! Ya puedes disfrutar de hasta 3% de cashback."}
    if tool_name == "consultar_cashback":
        return {"user_id": uid, "periodo": args.get("periodo", "ultimo_mes"),
                "cashback_generado": round(rng.uniform(20, 800), 2),
                "cashback_disponible": round(rng.uniform(10, 500), 2),
                "transacciones_con_cashback": rng.randint(5, 40)}
    if tool_name == "listar_ofertas_personalizadas":
        n = rng.randint(2, 5)
        return {"user_id": uid, "ofertas": rng.sample(OFERTAS, min(n, len(OFERTAS)))}
    return {"error": f"Tool {tool_name} not found"}
