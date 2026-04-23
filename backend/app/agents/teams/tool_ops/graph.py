from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.agents.teams.tool_ops.agents import (
    craft_tool_response,
    execute_tool_request,
    prepare_tool_request,
)


class ToolOpsState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str
    team_iterations: int
    tool_request: str
    tool_result: dict[str, Any]


def build_tool_ops_subgraph():
    workflow = StateGraph(ToolOpsState)
    workflow.add_node("tool_plan", prepare_tool_request)
    workflow.add_node("tool_execute", execute_tool_request)
    workflow.add_node("tool_respond", craft_tool_response)

    workflow.add_edge(START, "tool_plan")
    workflow.add_edge("tool_plan", "tool_execute")
    workflow.add_edge("tool_execute", "tool_respond")
    workflow.add_edge("tool_respond", END)

    return workflow.compile()
