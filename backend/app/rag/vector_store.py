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
        if self._index is None or self._embedder is None or not query:
            return []
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
            logger.exception("hybrid_search falló")
            return []
