from __future__ import annotations

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class GlobalState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str
    global_iterations: int
