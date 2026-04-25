from __future__ import annotations

from collections import defaultdict
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings


class InMemoryAsyncRedis:
    """Simple async Redis substitute used for tests and fallback mode."""

    def __init__(self) -> None:
        self._kv: dict[str, Any] = {}
        self._counters: defaultdict[str, int] = defaultdict(int)

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> Any:
        return self._kv.get(key)

    async def set(self, key: str, value: Any) -> bool:
        self._kv[key] = value
        return True

    async def incr(self, key: str) -> int:
        self._counters[key] += 1
        return self._counters[key]

    async def expire(self, key: str, seconds: int) -> bool:
        # TTL behavior is not simulated for tests.
        _ = seconds
        return key in self._counters or key in self._kv

    async def aclose(self) -> None:
        self._kv.clear()
        self._counters.clear()


def create_redis_client(settings: Settings) -> Redis | InMemoryAsyncRedis:
    if settings.testing:
        return InMemoryAsyncRedis()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def verify_redis_connection(redis_client: Redis | InMemoryAsyncRedis) -> bool:
    try:
        return bool(await redis_client.ping())
    except (RedisError, OSError):
        return False
