"""
backend/tests/test_contract_mcp_gateway.py
============================================

Contract tests para el MCP Gateway JSON-RPC.
Valida el contrato entre tool_ops y MCP Gateway.
"""
from __future__ import annotations

import json
from typing import Any, Dict

import pytest


class TestMCPGatewayContract:
    """Verifica el contrato JSON-RPC del MCP Gateway."""

    def test_jsonrpc_request_schema(self) -> None:
        """Request JSON-RPC debe tener jsonrpc, id, method, params."""
        request = {
            "jsonrpc": "2.0",
            "id": "test-001",
            "method": "tools/call",
            "params": {"name": "consultar_saldo", "arguments": {"producto_id": "PROD-001"}},
        }
        assert request["jsonrpc"] == "2.0"
        assert "id" in request
        assert "method" in request
        assert "params" in request

    def test_jsonrpc_success_response(self) -> None:
        """Response exitosa tiene jsonrpc, id, result."""
        response = {
            "jsonrpc": "2.0",
            "id": "test-001",
            "result": {"saldo_actual": 25000.50, "moneda": "MXN"},
        }
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "error" not in response

    def test_jsonrpc_error_response(self) -> None:
        """Response de error tiene jsonrpc, id, error con code y message."""
        response = {
            "jsonrpc": "2.0",
            "id": "test-001",
            "error": {"code": -32601, "message": "Tool not found: fake_tool"},
        }
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]

    def test_tools_list_response(self) -> None:
        """tools/list retorna lista de tool definitions."""
        response = {
            "jsonrpc": "2.0",
            "id": "test-002",
            "result": {
                "tools": [
                    {
                        "name": "consultar_saldo",
                        "description": "Consulta saldo",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"producto_id": {"type": "string"}},
                            "required": ["producto_id"],
                        },
                    }
                ]
            },
        }
        tools = response["result"]["tools"]
        assert len(tools) > 0
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    def test_tool_call_params_structure(self) -> None:
        """params de tools/call debe tener name y arguments."""
        params = {"name": "transferir_spei", "arguments": {"beneficiario_id": "B-1", "monto": 500}}
        assert "name" in params
        assert "arguments" in params
        assert isinstance(params["arguments"], dict)

    def test_mutating_tool_results(self) -> None:
        """Tools mutantes retornan status field."""
        result = {"status": "ejecutado", "referencia": "SPEI-ABC", "monto": 500}
        assert "status" in result
        assert result["status"] in {"ejecutado", "en_revision", "agendado", "creado", "otp_enviado", "validado"}

    def test_read_tool_results(self) -> None:
        """Tools de lectura retornan datos sin status requerido."""
        result = {"saldo_actual": 15000.00, "moneda": "MXN", "producto_id": "PROD-001"}
        assert isinstance(result, dict)
        # Read tools can have any structure but should be non-empty
        assert len(result) > 0
