from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import uuid4


class MCPClient:
    """Minimal async JSON-RPC client for line-delimited MCP transports."""

    def __init__(self, host: str, port: int, timeout_seconds: float = 5.0) -> None:
        self.host = host
        self.port = port
        self.timeout_seconds = timeout_seconds
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def __aenter__(self) -> MCPClient:
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        if self._reader is not None and self._writer is not None:
            return
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            timeout=self.timeout_seconds,
        )

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None

    async def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        if self._reader is None or self._writer is None:
            await self.connect()

        request_id = str(uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }

        assert self._writer is not None
        self._writer.write((json.dumps(payload, ensure_ascii=True) + "\n").encode("utf-8"))
        await self._writer.drain()

        assert self._reader is not None
        raw_response = await asyncio.wait_for(
            self._reader.readline(),
            timeout=self.timeout_seconds,
        )
        if not raw_response:
            raise ConnectionError("MCP server closed the connection before sending a response")

        response = json.loads(raw_response.decode("utf-8"))
        if "error" in response:
            raise RuntimeError(f"MCP call failed: {response['error']}")
        return response.get("result")

    async def list_tools(self) -> dict[str, Any]:
        result = await self.call("tools/list")
        return result if isinstance(result, dict) else {"tools": []}
