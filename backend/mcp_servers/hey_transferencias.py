"""
backend/mcp_servers/hey_transferencias.py
==========================================
MCP Server: hey-transferencias — SPEI, CoDi, agendados.
"""
from __future__ import annotations
import hashlib
from typing import Any, Dict

TOOLS = [
    {"name": "transferir_spei", "description": "Transferencia SPEI. MUTANTE + step-up si actividad_atipica.",
     "inputSchema": {"type": "object", "properties": {"beneficiario_id": {"type": "string"}, "monto": {"type": "number"}, "concepto": {"type": "string"}}, "required": ["beneficiario_id", "monto"]}},
    {"name": "agendar_transferencia", "description": "Agendar transferencia futura. MUTANTE.",
     "inputSchema": {"type": "object", "properties": {"beneficiario_id": {"type": "string"}, "monto": {"type": "number"}, "concepto": {"type": "string"}, "fecha": {"type": "string"}}, "required": ["beneficiario_id", "monto", "fecha"]}},
    {"name": "generar_qr_codi", "description": "Genera QR CoDi para cobrar.",
     "inputSchema": {"type": "object", "properties": {"monto": {"type": "number"}, "concepto": {"type": "string"}}, "required": ["monto"]}},
    {"name": "escanear_codi", "description": "Escanea un QR CoDi para pagar.",
     "inputSchema": {"type": "object", "properties": {"qr_payload": {"type": "string"}}, "required": ["qr_payload"]}},
]

async def handle(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "transferir_spei":
        m = args.get("monto", 0)
        ref = hashlib.md5(f"{args.get('beneficiario_id','')}{m}".encode()).hexdigest()[:8].upper()  # noqa: S324
        return {"status": "ejecutado", "beneficiario_id": args.get("beneficiario_id"),
                "monto": m, "concepto": args.get("concepto", ""), "referencia": f"SPEI-{ref}",
                "mensaje": f"Transferencia SPEI de ${m:,.2f} MXN enviada."}
    if tool_name == "agendar_transferencia":
        return {"status": "agendado", "beneficiario_id": args.get("beneficiario_id"),
                "monto": args.get("monto"), "fecha": args.get("fecha"),
                "mensaje": f"Transferencia agendada para {args.get('fecha')}."}
    if tool_name == "generar_qr_codi":
        m = args.get("monto", 0)
        qr = hashlib.sha256(f"CODI:{m}:{args.get('concepto','')}".encode()).hexdigest()[:20]
        return {"qr_data": qr, "monto": m, "concepto": args.get("concepto", ""),
                "mensaje": f"QR CoDi generado por ${m:,.2f} MXN."}
    if tool_name == "escanear_codi":
        return {"status": "procesado", "qr_payload": args.get("qr_payload", ""),
                "mensaje": "Pago CoDi procesado exitosamente."}
    return {"error": f"Tool {tool_name} not found"}
