from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

try:
    from redisvl.index import SearchIndex
    from redisvl.query import TextQuery, VectorQuery
except ImportError:
    SearchIndex = None  # type: ignore[assignment]
    TextQuery = None  # type: ignore[assignment]
    VectorQuery = None  # type: ignore[assignment]


@dataclass(slots=True)
class IndexedDocument:
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SearchHit:
    id: str
    text: str
    metadata: dict[str, Any]
    dense_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0


class RedisHybridVectorStore:
    def __init__(
        self,
        redis_url: str,
        index_name: str,
        prefix: str,
        vector_dims: int,
    ) -> None:
        if SearchIndex is None or TextQuery is None or VectorQuery is None:
            raise ImportError(
                "RedisVL is not available. Install redisvl to use hybrid retrieval."
            )

        self.redis_url = redis_url
        self.index_name = index_name
        self.prefix = prefix
        self.vector_dims = vector_dims

        self._index = SearchIndex.from_dict(self._build_schema())
        if hasattr(self._index, "connect"):
            self._index.connect(redis_url=self.redis_url)

    def _build_schema(self) -> dict[str, Any]:
        return {
            "index": {
                "name": self.index_name,
                "prefix": self.prefix,
                "storage_type": "hash",
            },
            "fields": [
                {"name": "id", "type": "tag"},
                {"name": "text", "type": "text"},
                {"name": "metadata", "type": "text"},
                {
                    "name": "embedding",
                    "type": "vector",
                    "attrs": {
                        "algorithm": "hnsw",
                        "datatype": "float32",
                        "dims": self.vector_dims,
                        "distance_metric": "cosine",
                    },
                },
            ],
        }

    async def initialize(self) -> None:
        try:
            await asyncio.to_thread(self._index.create)
        except (RuntimeError, ValueError) as exc:
            if "exists" not in str(exc).lower():
                raise

    async def upsert_documents(self, documents: Iterable[IndexedDocument]) -> None:
        payload = [
            {
                "id": doc.id,
                "text": doc.text,
                "metadata": json.dumps(doc.metadata, ensure_ascii=True),
                "embedding": doc.embedding,
            }
            for doc in documents
        ]
        if not payload:
            return
        await asyncio.to_thread(self._index.load, payload, id_field="id")

    async def dense_search(self, query_embedding: list[float], top_k: int = 8) -> list[SearchHit]:
        query = VectorQuery(
            vector=query_embedding,
            vector_field_name="embedding",
            return_fields=["id", "text", "metadata"],
            num_results=top_k,
        )
        raw = await asyncio.to_thread(self._index.query, query)
        return self._to_hits(raw, mode="dense")

    async def bm25_search(self, query_text: str, top_k: int = 8) -> list[SearchHit]:
        query = TextQuery(
            query_text,
            return_fields=["id", "text", "metadata"],
            num_results=top_k,
        )
        raw = await asyncio.to_thread(self._index.query, query)
        return self._to_hits(raw, mode="bm25")

    async def hybrid_search(
        self,
        query_text: str,
        query_embedding: list[float],
        top_k: int = 8,
    ) -> list[SearchHit]:
        dense_hits, bm25_hits = await asyncio.gather(
            self.dense_search(query_embedding, top_k=top_k),
            self.bm25_search(query_text, top_k=top_k),
        )

        merged: dict[str, SearchHit] = {hit.id: hit for hit in dense_hits}
        for bm25_hit in bm25_hits:
            if bm25_hit.id in merged:
                merged[bm25_hit.id].bm25_score = bm25_hit.bm25_score
            else:
                merged[bm25_hit.id] = bm25_hit
        return list(merged.values())

    def _to_hits(self, raw: Any, mode: str) -> list[SearchHit]:
        rows = raw
        if isinstance(raw, dict) and "results" in raw:
            rows = raw["results"]
        if not isinstance(rows, list):
            return []

        hits: list[SearchHit] = []
        for row in rows:
            if not isinstance(row, dict):
                continue

            metadata_raw = row.get("metadata") or "{}"
            try:
                metadata = json.loads(metadata_raw) if isinstance(metadata_raw, str) else metadata_raw
            except json.JSONDecodeError:
                metadata = {"raw": metadata_raw}

            score = float(
                row.get("score")
                or row.get("vector_distance")
                or row.get("__score")
                or 0.0
            )
            hit = SearchHit(
                id=str(row.get("id", "unknown")),
                text=str(row.get("text", "")),
                metadata=metadata if isinstance(metadata, dict) else {},
            )
            if mode == "dense":
                hit.dense_score = score
            else:
                hit.bm25_score = score
            hits.append(hit)

        return hits
