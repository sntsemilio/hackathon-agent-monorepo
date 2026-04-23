from __future__ import annotations

import re
from collections.abc import Sequence

from app.rag.vector_store import SearchHit


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if token}


async def simulate_rerank(query: str, hits: Sequence[SearchHit], top_k: int = 5) -> list[SearchHit]:
    """Simulate a re-ranker pass by blending lexical overlap with hybrid retrieval scores."""

    query_tokens = _tokenize(query)
    reranked = list(hits)

    for hit in reranked:
        content_tokens = _tokenize(hit.text)
        overlap_ratio = (
            len(query_tokens.intersection(content_tokens)) / max(len(query_tokens), 1)
            if query_tokens
            else 0.0
        )

        dense_component = max(0.0, 1.0 - hit.dense_score)
        bm25_component = max(0.0, hit.bm25_score)
        hit.rerank_score = round(
            (0.45 * dense_component) + (0.35 * bm25_component) + (0.20 * overlap_ratio),
            6,
        )

    reranked.sort(key=lambda item: item.rerank_score, reverse=True)
    return reranked[:top_k]
