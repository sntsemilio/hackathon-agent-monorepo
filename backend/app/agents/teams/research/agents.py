from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.agents.micro_agents.summarizer_slm import summarize_with_slm
from app.agents.teams.research.state import (
    ResearchContext,
    ResearchDraft,
    ResearchPlan,
    ResearchState,
    RetrievedDocument,
)
from app.rag.retrieval import get_hybrid_retriever


def _message_to_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    return str(content)


def _latest_user_query(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            text = _message_to_text(message).strip()
            if text:
                return text
    if messages:
        return _message_to_text(messages[-1]).strip()
    return "No query provided."


async def plan_research(state: ResearchState) -> dict[str, Any]:
    query = _latest_user_query(state.get("messages", []))
    plan = ResearchPlan(
        query=query,
        requires_vision=bool(state.get("base64_images")),
        top_k=15,
    )
    return {
        "plan": plan.model_dump(),
        "team_iterations": state.get("team_iterations", 0) + 1,
    }


async def gather_context(state: ResearchState) -> dict[str, Any]:
    plan = ResearchPlan.model_validate(state.get("plan", {}))
    vision_notes = state.get("vision_notes", [])

    retriever = await get_hybrid_retriever()
    hits = await retriever.retrieve(query=plan.query, top_k=plan.top_k)

    documents: list[RetrievedDocument] = []
    for hit in hits:
        documents.append(
            RetrievedDocument(
                doc_id=hit.id,
                text=hit.text,
                metadata=hit.metadata,
                dense_score=hit.dense_score,
                bm25_score=hit.bm25_score,
                rerank_score=hit.rerank_score,
            )
        )

    context = ResearchContext(
        plan=plan,
        documents=documents,
        vision_notes=[str(item) for item in vision_notes],
    )

    return {
        "context": context.model_dump(),
    }


async def draft_research_response(state: ResearchState) -> dict[str, Any]:
    context = ResearchContext.model_validate(state.get("context", {}))
    evidence = [doc.text for doc in context.documents]
    response = await summarize_with_slm(
        query=context.plan.query,
        evidence=evidence,
        vision_notes=context.vision_notes,
    )

    citations = [doc.doc_id for doc in context.documents[:3]]
    metrics: dict[str, float | int] = {
        "hybrid_candidates": len(context.documents),
        "reranked_returned": min(3, len(context.documents)),
    }
    draft = ResearchDraft(answer=response, citations=citations, rag_metrics=metrics)

    return {
        "draft": draft.model_dump(),
        "rag_metrics": metrics,
        "messages": [AIMessage(content=response)],
    }
