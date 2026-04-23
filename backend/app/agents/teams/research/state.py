from __future__ import annotations

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ResearchState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str
    team_iterations: int
    query: str
    notes: list[str]
    context_snippets: list[str]
    draft_answer: str
