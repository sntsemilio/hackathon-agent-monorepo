from __future__ import annotations

from typing import Annotated
from typing import Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class ResearchPlan(BaseModel):
    query: str = Field(min_length=1)
    requires_vision: bool = False
    top_k: int = Field(default=15, ge=1, le=50)


class RetrievedDocument(BaseModel):
    doc_id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    dense_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0


class ResearchContext(BaseModel):
    plan: ResearchPlan
    documents: list[RetrievedDocument] = Field(default_factory=list)
    vision_notes: list[str] = Field(default_factory=list)


class ResearchDraft(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    rag_metrics: dict[str, float | int] = Field(default_factory=dict)


class ResearchState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str
    base64_images: list[str]
    vision_notes: list[str]
    team_iterations: int
    plan: dict[str, Any]
    context: dict[str, Any]
    draft: dict[str, Any]
    rag_metrics: dict[str, float | int]
