"""
backend/app/core/database.py
=============================

Operaciones Redis. Wrapper async sobre `redis.asyncio`.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


async def create_redis_client(url: str) -> aioredis.Redis:
    """Crea y verifica un cliente Redis async."""
    client = aioredis.from_url(url, decode_responses=True)
    pong = await client.ping()
    if not pong:
        raise RuntimeError(f"Redis ping falló en {url}")
    logger.info("Redis conectado: %s", url)
    return client


async def get_ficha(client: aioredis.Redis, user_id: str, prefix: str = "ficha:") -> Optional[str]:
    return await client.get(f"{prefix}{user_id}")


async def set_ficha(client: aioredis.Redis, user_id: str, payload: str,
                    prefix: str = "ficha:", ttl_seconds: int = 0) -> None:
    key = f"{prefix}{user_id}"
    if ttl_seconds > 0:
        await client.setex(key, ttl_seconds, payload)
    else:
        await client.set(key, payload)
