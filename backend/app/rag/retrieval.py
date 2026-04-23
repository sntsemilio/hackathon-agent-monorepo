from __future__ import annotations

import asyncio
import hashlib

from app.core.config import get_settings
from app.rag.re_ranker import simulate_rerank
from app.rag.vector_store import RedisHybridVectorStore, SearchHit


class HybridRetriever:
    def __init__(self, store: RedisHybridVectorStore, embedding_dims: int) -> None:
        self._store = store
        self._embedding_dims = embedding_dims

    async def retrieve(self, query: str, top_k: int = 6) -> list[SearchHit]:
        query_embedding = self._hash_embed(query)
        merged_hits = await self._store.hybrid_search(
            query_text=query,
            query_embedding=query_embedding,
            top_k=max(top_k * 2, top_k),
        )
        return await simulate_rerank(query=query, hits=merged_hits, top_k=top_k)

    def _hash_embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < self._embedding_dims:
            for byte in digest:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) >= self._embedding_dims:
                    break
        return values


_retriever_lock = asyncio.Lock()
_retriever_holder: dict[str, HybridRetriever] = {}


async def get_hybrid_retriever() -> HybridRetriever:
    cached = _retriever_holder.get("instance")
    if cached is not None:
        return cached

    async with _retriever_lock:
        cached = _retriever_holder.get("instance")
        if cached is None:
            settings = get_settings()
            store = RedisHybridVectorStore(
                redis_url=settings.redis_url,
                index_name=settings.redis_index_name,
                prefix=settings.redis_prefix,
                vector_dims=settings.redis_vector_dims,
            )
            await store.initialize()
            cached = HybridRetriever(store=store, embedding_dims=settings.redis_vector_dims)
            _retriever_holder["instance"] = cached

    return cached
