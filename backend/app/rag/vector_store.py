"""
backend/app/rag/vector_store.py
================================

Vector store sobre Redis con RedisVL HNSW (hybrid search texto + vector).

Uso desde el agente:
    store = VectorStore()
    hits = await store.hybrid_search("¿cómo activo Hey Pro?", top_k=5)

Diseño:
  - El índice se llama por settings.REDIS_INDEX_NAME (default: "havi_kb").
  - Si RedisVL no está instalado o el índice no existe, devuelve [] sin romper.
  - El backfill del índice se hace con un script aparte (no incluido aquí).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class SearchHit:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    dense_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Wrapper sobre redisvl.SearchIndex. Tolerante a falta de instalación."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._index = None
        self._embedder = None
        self._tried = False

    def _try_init(self) -> None:
        if self._tried:
            return
        self._tried = True
        try:
            from redisvl.index import AsyncSearchIndex
            from redisvl.utils.vectorize import HFTextVectorizer

            self._embedder = HFTextVectorizer(model=self.settings.EMBED_MODEL)
            self._index = AsyncSearchIndex.from_existing(
                name=self.settings.REDIS_INDEX_NAME,
                redis_url=self.settings.REDIS_URL,
            )
            logger.info("RedisVL index conectado: %s", self.settings.REDIS_INDEX_NAME)
        except Exception:
            logger.warning("RedisVL no disponible o índice no creado — devolveré [].",
                           exc_info=True)
            self._index = None

    async def hybrid_search(self, query: str, top_k: int = 5,
                            filter_expr: Optional[str] = None) -> List[Dict[str, Any]]:
        self._try_init()
        if not query:
            return []

        # Try vector search first
        if self._index is not None and self._embedder is not None:
            try:
                from redisvl.query import VectorQuery
                vec = self._embedder.embed(query, as_buffer=True)
                q = VectorQuery(
                    vector=vec,
                    vector_field_name="embedding",
                    num_results=top_k,
                    return_fields=["text", "title", "source"],
                )
                if filter_expr:
                    q.set_filter(filter_expr)
                result = await self._index.query(q)
                return [dict(r) for r in result]
            except Exception:
                logger.warning("Vector search falló, usando fallback BM25")

        # Fallback: simple text search in Redis
        try:
            from redis import Redis
            r = Redis.from_url(self.settings.REDIS_URL, decode_responses=True)
            keywords = query.lower().split()
            matches = []

            # Search all doc: keys
            for key in r.scan_iter("doc:*"):
                doc = r.hgetall(key)
                text = doc.get("text", "").lower()
                score = sum(1 for kw in keywords if kw in text)
                if score > 0:
                    matches.append({
                        "id": key,
                        "text": doc.get("text", ""),
                        "title": doc.get("title", ""),
                        "source": doc.get("source", ""),
                        "score": score,
                    })

            r.close()
            # Sort by score and return top_k
            matches.sort(key=lambda x: x["score"], reverse=True)
            return matches[:top_k]
        except Exception:
            logger.exception("BM25 fallback también falló")
            return []
