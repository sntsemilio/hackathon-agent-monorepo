from __future__ import annotations

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict


class GlobalState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str
    global_iterations: int
    active_team: str
    base64_images: NotRequired[list[str]]
    blocked: NotRequired[bool]
    security_violation: NotRequired[str]
    delegation_trace: NotRequired[list[str]]
    final_response: NotRequired[str]
    rag_metrics: NotRequired[dict[str, float | int]]
