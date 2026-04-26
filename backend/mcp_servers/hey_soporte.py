"""
backend/mcp_servers/hey_soporte.py
====================================
MCP Server: hey-soporte — Tickets, reestructura, asesoría.
"""
from __future__ import annotations
import hashlib
from typing import Any, Dict

TOOLS = [
    {"name": "crear_ticket", "description": "Crea ticket de soporte. MUTANTE.",
     "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "asunto": {"type": "string"}, "prioridad": {"type": "string"}}, "required": ["user_id", "asunto"]}},
    {"name": "solicitar_reestructura", "description": "Solicita reestructura de crédito. MUTANTE.",
     "inputSchema": {"type": "object", "properties": {"credito_id": {"type": "string"}, "plan_propuesto": {"type": "string"}}, "required": ["credito_id"]}},
    {"name": "agendar_asesoria", "description": "Agenda asesoría financiera. MUTANTE.",
     "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "slot": {"type": "string"}}, "required": ["user_id", "slot"]}},
]

async def handle(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "crear_ticket":
        ref = hashlib.md5(f"{args.get('user_id','')}{args.get('asunto','')}".encode()).hexdigest()[:6].upper()  # noqa: S324
        return {"status": "creado", "ticket_id": f"TKT-{ref}",
                "user_id": args.get("user_id"), "asunto": args.get("asunto"),
                "prioridad": args.get("prioridad", "media"),
                "mensaje": f"Ticket TKT-{ref} creado. Te contactaremos en menos de 24 hrs."}
    if tool_name == "solicitar_reestructura":
        return {"status": "en_revision", "credito_id": args.get("credito_id"),
                "plan_propuesto": args.get("plan_propuesto", "reduccion_mensualidad"),
                "mensaje": "Tu solicitud de reestructura está en revisión. Un asesor te contactará."}
    if tool_name == "agendar_asesoria":
        return {"status": "agendado", "user_id": args.get("user_id"),
                "slot": args.get("slot"), "asesor": "María González",
                "mensaje": f"Asesoría agendada para {args.get('slot')}. Te esperamos."}
    return {"error": f"Tool {tool_name} not found"}
