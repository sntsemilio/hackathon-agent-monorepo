"""
backend/mcp_servers/hey_inversion.py
=====================================
MCP Server: hey-inversion — Tools de inversión y rendimientos.
"""
from __future__ import annotations
import hashlib, random
from typing import Any, Dict

TOOLS = [
    {"name": "consultar_posicion", "description": "Consulta posición de inversión.",
     "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}},
    {"name": "consultar_gat", "description": "Consulta GAT de un producto.",
     "inputSchema": {"type": "object", "properties": {"producto_id": {"type": "string"}}, "required": ["producto_id"]}},
    {"name": "abonar_inversion", "description": "Abona a inversión. MUTANTE.",
     "inputSchema": {"type": "object", "properties": {"producto_id": {"type": "string"}, "monto": {"type": "number"}}, "required": ["producto_id", "monto"]}},
    {"name": "retirar_inversion", "description": "Retira de inversión. MUTANTE.",
     "inputSchema": {"type": "object", "properties": {"producto_id": {"type": "string"}, "monto": {"type": "number"}}, "required": ["producto_id", "monto"]}},
    {"name": "simular_rendimiento", "description": "Simula rendimiento a plazo.",
     "inputSchema": {"type": "object", "properties": {"monto": {"type": "number"}, "plazo": {"type": "integer"}, "tipo": {"type": "string"}}, "required": ["monto", "plazo"]}},
]

def _seed(s: str) -> random.Random:
    return random.Random(int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big"))

async def handle(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "consultar_posicion":
        rng = _seed(args.get("user_id", "USR"))
        cap = round(rng.uniform(5000, 500000), 2)
        rend = round(cap * rng.uniform(0.02, 0.12), 2)
        return {"user_id": args.get("user_id"), "capital_invertido": cap, "rendimiento_acumulado": rend,
                "valor_actual": round(cap + rend, 2), "gat_nominal": f"{round(rng.uniform(8,15),2)}%",
                "productos": [{"nombre": "Hey Inversión", "monto": round(cap*0.6,2)}, {"nombre": "Pagaré 28d", "monto": round(cap*0.4,2)}]}
    if tool_name == "consultar_gat":
        rng = _seed(args.get("producto_id", "INV"))
        return {"producto_id": args.get("producto_id"), "gat_nominal": f"{round(rng.uniform(9,15),2)}%",
                "gat_real": f"{round(rng.uniform(5,10),2)}%", "plazo_minimo_dias": 1, "monto_minimo": 100.0}
    if tool_name == "abonar_inversion":
        m = args.get("monto", 0)
        return {"status": "ejecutado", "producto_id": args.get("producto_id"), "monto_abonado": m,
                "mensaje": f"Abono de ${m:,.2f} MXN realizado."}
    if tool_name == "retirar_inversion":
        m = args.get("monto", 0)
        return {"status": "ejecutado", "producto_id": args.get("producto_id"), "monto_retirado": m,
                "mensaje": f"Retiro de ${m:,.2f} MXN procesado."}
    if tool_name == "simular_rendimiento":
        m, p = args.get("monto", 10000), args.get("plazo", 90)
        t = 0.12 if args.get("tipo") == "hey_inversion" else 0.10
        r = round(m * (t/365) * p, 2)
        return {"monto_inicial": m, "plazo_dias": p, "tasa_anual": f"{t*100:.1f}%",
                "rendimiento_estimado": r, "valor_final": round(m+r, 2)}
    return {"error": f"Tool {tool_name} not found"}
