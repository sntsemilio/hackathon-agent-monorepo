from __future__ import annotations

import pytest

from app.rag.re_ranker import CrossEncoderReRanker
from app.rag.vector_store import SearchHit


@pytest.mark.asyncio
async def test_reranker_returns_top_three(monkeypatch) -> None:
    monkeypatch.setattr("app.rag.re_ranker.CrossEncoder", None)

    hits = [
        SearchHit(
            id=f"doc-{idx}",
            text=f"Hybrid retrieval context chunk {idx}",
            metadata={},
            dense_score=0.1 + (idx * 0.01),
            bm25_score=1.0 / (idx + 1),
        )
        for idx in range(15)
    ]

    reranker = CrossEncoderReRanker()
    final_hits = await reranker.rerank(
        query="hybrid retrieval reranking",
        hits=hits,
        candidate_top_k=15,
        final_top_k=3,
    )

    assert len(final_hits) == 3
    assert final_hits[0].rerank_score >= final_hits[-1].rerank_score
