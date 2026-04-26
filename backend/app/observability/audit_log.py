"""
backend/app/observability/audit_log.py
=======================================

Audit logger que escribe a Redis list ``audit:{user_id}`` con JSON
estructurado. Cada entrada registra intent, tool, parámetros, resultado
y trace del nodo.

Para el demo también mantiene un buffer in-memory como fallback.
"""
from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """Escribe audit trail a Redis y mantiene fallback in-memory."""

    def __init__(self, history_limit: int = 200) -> None:
        self._memory: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._history_limit = history_limit

    async def log_event(
        self,
        redis_client: Any,
        user_id: str,
        session_id: str,
        event_type: str,
        intent: str = "",
        tool: str = "",
        tool_params: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        node_trace: Optional[List[Dict[str, Any]]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "session_id": session_id,
            "event_type": event_type,
            "intent": intent,
            "tool": tool,
            "tool_params": tool_params or {},
            "result": result or {},
            "node_trace": node_trace or [],
            **(extra or {}),
        }

        # In-memory always
        self._memory[user_id].append(entry)
        if len(self._memory[user_id]) > self._history_limit:
            self._memory[user_id] = self._memory[user_id][-self._history_limit:]

        # Redis
        if redis_client is not None:
            try:
                key = f"audit:{user_id}"
                await _redis_rpush(redis_client, key, json.dumps(entry, default=str))
                await _redis_ltrim(redis_client, key, -self._history_limit, -1)
            except Exception:
                logger.exception("audit_log: error escribiendo a Redis")

        logger.info(
            "audit: user=%s event=%s tool=%s",
            user_id, event_type, tool,
        )
        return entry

    async def get_audit_trail(
        self,
        redis_client: Any,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        # Try Redis first
        if redis_client is not None:
            try:
                key = f"audit:{user_id}"
                raw_entries = await _redis_lrange(redis_client, key, -limit, -1)
                if raw_entries:
                    return [json.loads(e) for e in raw_entries]
            except Exception:
                logger.exception("audit_log: error leyendo de Redis")

        # Fallback to memory
        return self._memory.get(user_id, [])[-limit:]

    def get_all_users(self) -> List[str]:
        return list(self._memory.keys())


# ---------------------------------------------------------------------------
# Redis helpers (async-compat)
# ---------------------------------------------------------------------------
async def _redis_rpush(client: Any, key: str, value: str) -> None:
    res = client.rpush(key, value)
    if hasattr(res, "__await__"):
        await res


async def _redis_ltrim(client: Any, key: str, start: int, end: int) -> None:
    res = client.ltrim(key, start, end)
    if hasattr(res, "__await__"):
        await res


async def _redis_lrange(client: Any, key: str, start: int, end: int) -> List[str]:
    res = client.lrange(key, start, end)
    if hasattr(res, "__await__"):
        res = await res
    return res if res else []


# Singleton global
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
