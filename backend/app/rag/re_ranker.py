from __future__ import annotations

import asyncio
import re
from collections.abc import Sequence

from app.core.config import get_settings
from app.rag.vector_store import SearchHit

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None  # type: ignore[assignment]


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if token}


class CrossEncoderReRanker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self._model_name = model_name
        self._model: CrossEncoder | None = None

    async def rerank(
        self,
        query: str,
        hits: Sequence[SearchHit],
        candidate_top_k: int,
        final_top_k: int,
    ) -> list[SearchHit]:
        candidates = list(hits)[:candidate_top_k]
        if not candidates:
            return []

        scores = await self._predict_scores(query, candidates)
        for hit, score in zip(candidates, scores, strict=False):
            hit.rerank_score = float(score)

        candidates.sort(key=lambda item: item.rerank_score, reverse=True)
        return candidates[:final_top_k]

    async def _predict_scores(self, query: str, hits: Sequence[SearchHit]) -> list[float]:
        if CrossEncoder is None:
            return _fallback_scores(query, hits)

        if self._model is None:
            self._model = await asyncio.to_thread(CrossEncoder, self._model_name)

        pairs = [[query, hit.text] for hit in hits]
        try:
            scores = await asyncio.to_thread(self._model.predict, pairs)
            return [float(score) for score in scores]
        except (RuntimeError, ValueError, TypeError):
            return _fallback_scores(query, hits)


def _fallback_scores(query: str, hits: Sequence[SearchHit]) -> list[float]:
    query_tokens = _tokenize(query)
    results: list[float] = []
    for hit in hits:
        content_tokens = _tokenize(hit.text)
        overlap_ratio = (
            len(query_tokens.intersection(content_tokens)) / max(len(query_tokens), 1)
            if query_tokens
            else 0.0
        )
        dense_component = max(0.0, 1.0 - hit.dense_score)
        bm25_component = max(0.0, hit.bm25_score)
        results.append((0.45 * dense_component) + (0.35 * bm25_component) + (0.20 * overlap_ratio))
    return results


_RERANKER_HOLDER: dict[str, CrossEncoderReRanker] = {}
_RERANKER_LOCK = asyncio.Lock()


async def get_cross_encoder_reranker() -> CrossEncoderReRanker:
    cached = _RERANKER_HOLDER.get("instance")
    if cached is not None:
        return cached

    async with _RERANKER_LOCK:
        cached = _RERANKER_HOLDER.get("instance")
        if cached is None:
            cached = CrossEncoderReRanker()
            _RERANKER_HOLDER["instance"] = cached
    return cached


async def rerank_top_k(query: str, hits: Sequence[SearchHit]) -> list[SearchHit]:
    settings = get_settings()
    reranker = await get_cross_encoder_reranker()
    return await reranker.rerank(
        query=query,
        hits=hits,
        candidate_top_k=settings.rag_dense_top_k,
        final_top_k=settings.rag_final_top_k,
    )


def build_rag_metrics(candidates: Sequence[SearchHit], final_hits: Sequence[SearchHit]) -> dict[str, float | int]:
    return {
        "hybrid_candidates": len(candidates),
        "reranked_returned": len(final_hits),
    }
