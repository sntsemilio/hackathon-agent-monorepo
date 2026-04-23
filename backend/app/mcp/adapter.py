from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field, create_model

from app.mcp.client import MCPClient


JSON_TYPE_TO_PYTHON: dict[str, type[Any]] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _safe_identifier(name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "mcp_tool"


def _build_args_schema(tool_name: str, input_schema: dict[str, Any]) -> type[BaseModel]:
    properties = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))
    field_definitions: dict[str, tuple[type[Any], Field]] = {}

    for field_name, field_schema in properties.items():
        field_type = JSON_TYPE_TO_PYTHON.get(field_schema.get("type", "string"), str)
        description = field_schema.get("description", "")
        if field_name in required:
            default = ...
        else:
            default = None
        field_definitions[field_name] = (
            field_type,
            Field(default=default, description=description),
        )

    model_name = f"{_safe_identifier(tool_name).title()}Args"
    return create_model(model_name, **field_definitions)


def adapt_mcp_definition_to_tool(client: MCPClient, definition: dict[str, Any]) -> BaseTool:
    """Convert an MCP tool definition JSON object into a LangChain @tool object."""

    tool_name = definition["name"]
    description = definition.get("description", f"MCP tool: {tool_name}")
    input_schema = definition.get("inputSchema", {"type": "object", "properties": {}})
    args_schema = _build_args_schema(tool_name, input_schema)

    async def _invoke_mcp_tool(**kwargs: Any) -> str:
        result = await client.call(
            "tools/call",
            {
                "name": tool_name,
                "arguments": kwargs,
            },
        )
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=True)

    _invoke_mcp_tool.__name__ = _safe_identifier(tool_name)
    _invoke_mcp_tool.__doc__ = description
    return tool(tool_name, description=description, args_schema=args_schema)(_invoke_mcp_tool)


async def load_mcp_tools(client: MCPClient) -> list[BaseTool]:
    manifest = await client.list_tools()
    definitions = manifest.get("tools", [])
    return [adapt_mcp_definition_to_tool(client, definition) for definition in definitions]
