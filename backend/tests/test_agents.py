from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from app.agents.micro_agents.guardrail_slm import guardrail_slm_node
from app.agents.supervisor import _route_after_profiler


@pytest.mark.asyncio
async def test_route_request_routes_to_tool_ops() -> None:
    state = {
        "profile": {"intent": "transferencia"},
    }
    routed = _route_after_profiler(state)
    assert routed == "tool_ops"


@pytest.mark.asyncio
async def test_guardrail_allows_safe_input() -> None:
    state = {
        "input_text": "Please summarize redis hybrid retrieval",
        "thread_id": "agent-thread-2",
        "ficha_cliente": {},
    }
    output = await guardrail_slm_node(state)
    assert output["guardrail"]["blocked"] is False
