"""
backend/mcp_servers/gateway.py
================================

MCP Gateway — FastAPI app que actúa como proxy JSON-RPC.
Rutea llamadas al MCP server correcto por namespace.

Corre en localhost:8765 (MCP_PORT del config).

Uso standalone:
    uvicorn mcp_servers.gateway:app --port 8765
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import all tool handlers
# ---------------------------------------------------------------------------
from mcp_servers.hey_cuentas import TOOLS as CUENTAS_TOOLS, handle as handle_cuentas
from mcp_servers.hey_credito import TOOLS as CREDITO_TOOLS, handle as handle_credito
from mcp_servers.hey_inversion import TOOLS as INVERSION_TOOLS, handle as handle_inversion
from mcp_servers.hey_transferencias import TOOLS as TRANSFERENCIAS_TOOLS, handle as handle_transferencias
from mcp_servers.hey_pro_shop import TOOLS as PRO_SHOP_TOOLS, handle as handle_pro_shop
from mcp_servers.hey_soporte import TOOLS as SOPORTE_TOOLS, handle as handle_soporte
from mcp_servers.hey_verificacion import TOOLS as VERIFICACION_TOOLS, handle as handle_verificacion

# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------
TOOL_HANDLERS: Dict[str, Any] = {}
ALL_TOOLS: list[Dict[str, Any]] = []

for tools, handler in [
    (CUENTAS_TOOLS, handle_cuentas),
    (CREDITO_TOOLS, handle_credito),
    (INVERSION_TOOLS, handle_inversion),
    (TRANSFERENCIAS_TOOLS, handle_transferencias),
    (PRO_SHOP_TOOLS, handle_pro_shop),
    (SOPORTE_TOOLS, handle_soporte),
    (VERIFICACION_TOOLS, handle_verificacion),
]:
    for tool_def in tools:
        TOOL_HANDLERS[tool_def["name"]] = handler
        ALL_TOOLS.append(tool_def)


# ---------------------------------------------------------------------------
# Gateway App
# ---------------------------------------------------------------------------
app = FastAPI(title="MCP Gateway · Hey Banco", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple rate limiter in-memory
_rate_counter: Dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 100


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str = ""
    method: str
    params: Dict[str, Any] = {}


def _check_rate_limit(client_id: str) -> bool:
    now = time.time()
    calls = _rate_counter.setdefault(client_id, [])
    _rate_counter[client_id] = [t for t in calls if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_counter[client_id]) >= RATE_LIMIT_MAX:
        return False
    _rate_counter[client_id].append(now)
    return True


@app.post("/rpc")
async def json_rpc(request: Request) -> Dict[str, Any]:
    """Endpoint JSON-RPC principal."""
    client_id = request.headers.get("X-Client-ID", "anonymous")
    if not _check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    body = await request.json()
    req = JsonRpcRequest(**body)

    # tools/list
    if req.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {"tools": ALL_TOOLS},
        }

    # tools/call
    if req.method == "tools/call":
        tool_name = req.params.get("name", "")
        arguments = req.params.get("arguments", {})
        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }
        try:
            result = await handler(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": result,
            }
        except Exception as exc:
            logger.exception("MCP tool call failed: %s", tool_name)
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "error": {"code": -32000, "message": str(exc)},
            }

    return {
        "jsonrpc": "2.0",
        "id": req.id,
        "error": {"code": -32601, "message": f"Method not found: {req.method}"},
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"ok": True, "tools_registered": len(ALL_TOOLS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
