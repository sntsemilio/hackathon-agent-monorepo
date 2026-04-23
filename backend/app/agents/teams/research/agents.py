from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.agents.teams.research.state import ResearchState
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
    notes = list(state.get("notes", []))
    notes.append("Prepared hybrid retrieval plan from user question.")
    return {
        "query": query,
        "team_iterations": state.get("team_iterations", 0) + 1,
        "notes": notes,
    }


async def gather_context(state: ResearchState) -> dict[str, Any]:
    query = state.get("query") or _latest_user_query(state.get("messages", []))
    notes = list(state.get("notes", []))

    retriever = await get_hybrid_retriever()
    hits = await retriever.retrieve(query=query, top_k=4)

    snippets: list[str] = []
    for hit in hits:
        snippets.append(
            (
                f"[{hit.id}] {hit.text} "
                f"(rerank={hit.rerank_score:.4f}, dense={hit.dense_score:.4f}, bm25={hit.bm25_score:.4f})"
            )
        )

    if not snippets:
        snippets.append("No indexed documents found in Redis. Falling back to reasoning-only answer.")

    notes.append(f"Retrieved {len(snippets)} snippets with hybrid search + simulated rerank.")
    return {
        "context_snippets": snippets,
        "notes": notes,
    }


async def draft_research_response(state: ResearchState) -> dict[str, Any]:
    query = state.get("query") or _latest_user_query(state.get("messages", []))
    snippets = state.get("context_snippets", [])

    evidence = "\n".join(f"- {snippet}" for snippet in snippets)
    if not evidence:
        evidence = "- No external evidence available."

    response = (
        "Research Team Findings\n"
        f"Question: {query}\n"
        "Evidence:\n"
        f"{evidence}\n"
        "Conclusion: This draft came from the research subgraph after hybrid retrieval and reranking."
    )

    return {
        "draft_answer": response,
        "messages": [AIMessage(content=response)],
    }
