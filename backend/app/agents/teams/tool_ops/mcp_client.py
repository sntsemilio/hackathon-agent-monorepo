"""
backend/app/agents/teams/tool_ops/mcp_client.py
=================================================

ToolOps MCP Client — wrapper inteligente sobre MCPClient que:
1. Carga tools.json al init para clasificar read vs write
2. Para tools de escritura: emite tool_call_intent (no ejecuta)
3. Para tools de lectura: ejecuta y retorna inmediatamente
4. Aplica reglas de negocio (presion_financiera bloquea ciertas tools)
5. Dispara step-up auth cuando el segmento lo requiere
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TOOLS_JSON_PATH = Path(__file__).parent / "tools.json"


class ToolRegistry:
    """Carga y consulta el registro estático de tools."""

    def __init__(self) -> None:
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if TOOLS_JSON_PATH.exists():
            with open(TOOLS_JSON_PATH) as f:
                data = json.load(f)
            for t in data.get("tools", []):
                self.tools[t["name"]] = t
            logger.info("ToolRegistry: %d tools cargadas", len(self.tools))
        else:
            logger.warning("tools.json no encontrado en %s", TOOLS_JSON_PATH)

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return self.tools.get(name)

    def is_mutating(self, name: str) -> bool:
        t = self.tools.get(name)
        return bool(t and t.get("mutates", False))

    def requires_step_up(self, name: str, segment: str) -> bool:
        t = self.tools.get(name)
        if not t:
            return False
        return segment in (t.get("requires_step_up") or [])

    def is_blocked(self, name: str, salud: str) -> bool:
        t = self.tools.get(name)
        if not t:
            return False
        return salud in (t.get("blocked_if_salud") or [])

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self.tools.values())


# Singleton
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


class ToolOpsResult:
    """Resultado de la evaluación de una tool call."""

    def __init__(
        self,
        tool_name: str,
        action: str,  # "execute" | "confirm" | "blocked" | "step_up"
        result: Optional[Dict[str, Any]] = None,
        tool_call_id: str = "",
        message: str = "",
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.tool_name = tool_name
        self.action = action
        self.result = result
        self.tool_call_id = tool_call_id or f"tc-{uuid.uuid4().hex[:12]}"
        self.message = message
        self.params = params or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "action": self.action,
            "tool_call_id": self.tool_call_id,
            "result": self.result,
            "message": self.message,
            "params": self.params,
        }


async def evaluate_tool_call(
    tool_name: str,
    params: Dict[str, Any],
    ficha: Dict[str, Any],
    mcp_gateway_url: str = "http://localhost:8765",
) -> ToolOpsResult:
    """
    Evalúa y opcionalmente ejecuta una tool call.

    Lógica:
    1. Si la tool está bloqueada por salud financiera → blocked
    2. Si requiere step-up por segmento conductual → step_up
    3. Si es mutante → confirm (emite intent, no ejecuta)
    4. Si es lectura → execute directamente
    """
    registry = get_tool_registry()
    segs = ficha.get("segmentos", {})
    salud_name = (segs.get("salud_financiera") or {}).get("name", "")
    cond_name = (segs.get("conductual") or {}).get("name", "")

    # 1. Check blocked
    if registry.is_blocked(tool_name, salud_name):
        alt = _suggest_alternative(tool_name, salud_name)
        return ToolOpsResult(
            tool_name=tool_name,
            action="blocked",
            message=f"Esta operación no está disponible para tu perfil financiero actual. {alt}",
            params=params,
        )

    # 2. Check step-up
    if registry.requires_step_up(tool_name, cond_name):
        return ToolOpsResult(
            tool_name=tool_name,
            action="step_up",
            message="Necesitamos verificar tu identidad antes de continuar.",
            params=params,
        )

    # 3. Check mutation
    if registry.is_mutating(tool_name):
        return ToolOpsResult(
            tool_name=tool_name,
            action="confirm",
            message="Esta operación requiere tu confirmación.",
            params=params,
        )

    # 4. Execute read tool directly via HTTP
    result = await _call_mcp_gateway(mcp_gateway_url, tool_name, params)
    return ToolOpsResult(
        tool_name=tool_name,
        action="execute",
        result=result,
        params=params,
    )


async def execute_confirmed_tool(
    tool_name: str,
    params: Dict[str, Any],
    mcp_gateway_url: str = "http://localhost:8765",
) -> Dict[str, Any]:
    """Ejecuta una tool ya confirmada por el usuario."""
    return await _call_mcp_gateway(mcp_gateway_url, tool_name, params)


async def _call_mcp_gateway(
    gateway_url: str, tool_name: str, params: Dict[str, Any]
) -> Dict[str, Any]:
    """Llama al MCP Gateway vía HTTP POST JSON-RPC."""
    import httpx

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": params},
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{gateway_url}/rpc", json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                return {"error": data["error"].get("message", "MCP call failed")}
            return data.get("result", {})
    except Exception as exc:
        logger.exception("MCP Gateway call failed: %s", tool_name)
        # Fallback: return mock for demo resilience
        return {"status": "mock_fallback", "tool": tool_name, "message": str(exc)}


def _suggest_alternative(tool_name: str, salud: str) -> str:
    if salud == "presion_financiera":
        if tool_name in ("solicitar_aumento_linea", "convertir_a_msi"):
            return "Te recomendamos crear un ticket de soporte o solicitar reestructura."
    return ""
