from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from app.agents.micro_agents.guardrail_slm import guardrail_node
from app.agents.supervisor import route_request


@pytest.mark.asyncio
async def test_route_request_falls_back_after_five_iterations() -> None:
    state = {
        "messages": [HumanMessage(content="normal request")],
        "thread_id": "agent-thread-1",
        "global_iterations": 5,
        "active_team": "supervisor",
        "delegation_trace": [],
    }
    routed = await route_request(state)
    assert routed["next_team"] == "END"
    assert "Global iteration budget" in routed["final_response"]


@pytest.mark.asyncio
async def test_guardrail_allows_safe_input() -> None:
    state = {
        "messages": [HumanMessage(content="Please summarize redis hybrid retrieval")],
        "thread_id": "agent-thread-2",
        "global_iterations": 0,
        "active_team": "guardrail",
        "delegation_trace": [],
    }
    output = await guardrail_node(state)
    assert output["blocked"] is False
