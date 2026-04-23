from __future__ import annotations

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings


def create_redis_client(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def verify_redis_connection(redis_client: Redis) -> bool:
    try:
        return bool(await redis_client.ping())
    except (RedisError, OSError):
        return False
