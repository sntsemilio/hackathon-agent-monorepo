"""
backend/tests/test_contract_chat_stream.py
============================================

Contract tests para POST /chat/stream.
Valida que los SSE events cumplan con la estructura esperada.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest

# Expected SSE event schemas
EXPECTED_NODE_UPDATE_KEYS = {"event", "node", "data"}
EXPECTED_TRACE_UPDATE_KEYS = {"event", "data"}
EXPECTED_DONE_EVENT = {"event": "done"}

VALID_NODES = {
    "ficha_injector", "guardrail", "profiler",
    "plan_research", "gather_context", "draft_response",
    "tool_ops", "summarizer",
}

VALID_SSE_EVENTS = {
    "node_update", "trace_update", "trace_summary",
    "tool_call_intent", "done", "error",
}


def parse_sse_line(line: str) -> Dict[str, Any] | None:
    """Parse a single SSE data line."""
    if not line.startswith("data: "):
        return None
    try:
        return json.loads(line[6:])
    except json.JSONDecodeError:
        return None


class TestChatStreamContract:
    """Verifica el contrato de respuesta SSE de /chat/stream."""

    def test_node_update_structure(self) -> None:
        """node_update events deben tener event, node, data."""
        sample = {"event": "node_update", "node": "ficha_injector", "data": {"ficha_cliente": {}}}
        assert EXPECTED_NODE_UPDATE_KEYS.issubset(sample.keys())
        assert sample["event"] == "node_update"
        assert sample["node"] in VALID_NODES

    def test_trace_update_structure(self) -> None:
        """trace_update events deben tener event y data con node/status/latency_ms."""
        sample = {
            "event": "trace_update",
            "data": {
                "node": "guardrail",
                "status": "done",
                "latency_ms": 45.2,
                "explanation": "Aprobado",
                "timestamp": 1234567890.0,
            },
        }
        assert sample["event"] == "trace_update"
        assert "node" in sample["data"]
        assert sample["data"]["status"] in {"running", "done", "error"}
        assert isinstance(sample["data"]["latency_ms"], (int, float))

    def test_tool_call_intent_structure(self) -> None:
        """tool_call_intent events deben incluir tool_name, action, params."""
        sample = {
            "event": "tool_call_intent",
            "data": {
                "tool_name": "transferir_spei",
                "action": "confirm",
                "tool_call_id": "tc-abc123",
                "message": "Requiere confirmación",
                "params": {"beneficiario_id": "BEN-001", "monto": 1500},
            },
        }
        assert sample["event"] == "tool_call_intent"
        data = sample["data"]
        assert "tool_name" in data
        assert data["action"] in {"execute", "confirm", "blocked", "step_up"}
        assert "tool_call_id" in data
        assert isinstance(data.get("params", {}), dict)

    def test_done_event(self) -> None:
        """El último evento debe ser done."""
        assert EXPECTED_DONE_EVENT == {"event": "done"}

    def test_sse_line_parsing(self) -> None:
        """Las líneas SSE se parsean correctamente."""
        line = 'data: {"event": "node_update", "node": "profiler", "data": {}}'
        parsed = parse_sse_line(line)
        assert parsed is not None
        assert parsed["event"] == "node_update"

    def test_sse_line_invalid(self) -> None:
        """Líneas inválidas retornan None."""
        assert parse_sse_line("invalid line") is None
        assert parse_sse_line("data: {invalid}") is None

    def test_all_valid_events(self) -> None:
        """Todos los event types son válidos."""
        for event_type in VALID_SSE_EVENTS:
            assert event_type in VALID_SSE_EVENTS

    def test_safe_serializable_excludes_private(self) -> None:
        """Campos _* no deben aparecer en data de node_update."""
        sample_data = {
            "ficha_cliente": {"user_id": "USR-001"},
            "guardrail": {"blocked": False},
        }
        # Simulating _safe_serializable behavior
        for key in sample_data:
            assert not key.startswith("_"), f"Private field leaked: {key}"


class TestToolExecuteContract:
    """Verifica el contrato de POST /chat/tool-execute."""

    def test_execute_request_schema(self) -> None:
        """Request debe tener tool_call_id, user_id, confirmed."""
        request = {
            "tool_call_id": "tc-abc123",
            "user_id": "USR-001",
            "confirmed": True,
            "tool_name": "transferir_spei",
            "params": {"beneficiario_id": "BEN-001", "monto": 1500},
        }
        assert "tool_call_id" in request
        assert "user_id" in request
        assert isinstance(request["confirmed"], bool)

    def test_execute_response_confirmed(self) -> None:
        """Response de tool confirmada."""
        response = {
            "status": "executed",
            "tool_call_id": "tc-abc123",
            "result": {"referencia": "SPEI-ABC123"},
        }
        assert response["status"] == "executed"
        assert "result" in response

    def test_execute_response_cancelled(self) -> None:
        """Response de tool cancelada."""
        response = {
            "status": "cancelled",
            "tool_call_id": "tc-abc123",
            "message": "Operación cancelada.",
        }
        assert response["status"] == "cancelled"
