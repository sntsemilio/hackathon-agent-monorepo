from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings


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


_REDIS_CLIENT_REGISTRY: dict[str, Redis | InMemoryAsyncRedis | None] = {
    "shared": None,
}


def create_redis_client(settings: Settings) -> Redis | InMemoryAsyncRedis:
    if settings.testing:
        return InMemoryAsyncRedis()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def verify_redis_connection(redis_client: Redis | InMemoryAsyncRedis) -> bool:
    try:
        return bool(await redis_client.ping())
    except (RedisError, OSError):
        return False


def set_shared_redis_client(redis_client: Redis | InMemoryAsyncRedis | None) -> None:
    """Store a shared redis client used by helper persistence utilities."""

    _REDIS_CLIENT_REGISTRY["shared"] = redis_client


def _profile_key(user_id: str, settings: Settings) -> str:
    normalized_user_id = user_id.strip() or "anonymous"
    return f"{settings.conversational_profile_prefix}{normalized_user_id}"


async def _resolve_redis_client() -> tuple[Redis | InMemoryAsyncRedis, bool]:
    shared_client = _REDIS_CLIENT_REGISTRY["shared"]
    if shared_client is not None:
        return shared_client, False

    settings = get_settings()
    return create_redis_client(settings), True


async def get_conversational_profile(user_id: str) -> dict[str, Any]:
    """Retrieve a persisted conversational profile from Redis."""

    settings = get_settings()
    redis_client, owns_client = await _resolve_redis_client()

    try:
        raw_value = await redis_client.get(_profile_key(user_id, settings))
    except (RedisError, OSError):
        raw_value = None
    finally:
        if owns_client:
            await redis_client.aclose()

    if raw_value is None:
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
    return {}


async def set_conversational_profile(user_id: str, profile_data: dict[str, Any]) -> None:
    """Persist a conversational profile in Redis using JSON serialization."""

    if not isinstance(profile_data, dict):
        return

    settings = get_settings()
    redis_client, owns_client = await _resolve_redis_client()

    try:
        serialized = json.dumps(profile_data, ensure_ascii=True)
        await redis_client.set(_profile_key(user_id, settings), serialized)
    except (RedisError, OSError, TypeError, ValueError):
        return
    finally:
        if owns_client:
            await redis_client.aclose()
