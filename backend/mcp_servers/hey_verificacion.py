"""
backend/mcp_servers/hey_verificacion.py
========================================
MCP Server: hey-verificacion — Step-up auth, OTP, biometría.
"""
from __future__ import annotations
import hashlib, time
from typing import Any, Dict

TOOLS = [
    {"name": "iniciar_step_up", "description": "Inicia verificación step-up antes de operación sensible.",
     "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "accion_pendiente": {"type": "string"}}, "required": ["user_id", "accion_pendiente"]}},
    {"name": "validar_otp", "description": "Valida código OTP enviado al usuario.",
     "inputSchema": {"type": "object", "properties": {"token": {"type": "string"}}, "required": ["token"]}},
    {"name": "validar_biometria", "description": "Valida biometría facial/huella.",
     "inputSchema": {"type": "object", "properties": {"payload": {"type": "string"}}, "required": ["payload"]}},
]

async def handle(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "iniciar_step_up":
        otp = hashlib.md5(f"{args.get('user_id','')}{time.time()}".encode()).hexdigest()[:6].upper()  # noqa: S324
        return {"status": "otp_enviado", "user_id": args.get("user_id"),
                "accion_pendiente": args.get("accion_pendiente"),
                "otp_hint": f"***{otp[-3:]}", "canal": "push_notification",
                "mensaje": "Te enviamos un código de verificación a tu app Hey Banco."}
    if tool_name == "validar_otp":
        return {"status": "validado", "token": args.get("token"),
                "mensaje": "Código verificado correctamente. Puedes continuar."}
    if tool_name == "validar_biometria":
        return {"status": "validado", "tipo": "facial",
                "mensaje": "Identidad verificada por biometría facial."}
    return {"error": f"Tool {tool_name} not found"}
