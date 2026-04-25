"""
backend/app/agents/state.py
============================

GlobalState del grafo LangGraph. Lo importan supervisor y todos los nodos.

Convenciones:
  - claves con prefijo `_` no se serializan al cliente SSE
    (`routes._safe_serializable` las filtra).
  - `ficha_cliente` es opcional: el grafo debe degradar a default si es None.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class GlobalState(TypedDict, total=False):
    # Inputs
    user_id: str
    session_id: str
    input_text: str
    metadata: Dict[str, Any]

    # Personalización
    ficha_cliente: Optional[Dict[str, Any]]

    # Runtime (no se serializan)
    _redis_client: Any
    _ficha_prefix: str
    _ficha_ttl_seconds: int

    # Buffers de los nodos
    messages: List[Dict[str, Any]]
    guardrail: Optional[Dict[str, Any]]
    profile: Optional[Dict[str, Any]]
    research_plan: Optional[Dict[str, Any]]
    research_context: Optional[List[Dict[str, Any]]]
    tool_results: Optional[List[Dict[str, Any]]]
    draft_response: Optional[str]
    draft_meta: Optional[Dict[str, Any]]
    final_response: Optional[str]


def empty_state() -> GlobalState:
    return GlobalState(
        user_id="",
        session_id="",
        input_text="",
        metadata={},
        ficha_cliente=None,
        messages=[],
        guardrail=None,
        profile=None,
        research_plan=None,
        research_context=None,
        tool_results=None,
        draft_response=None,
        draft_meta=None,
        final_response=None,
    )
