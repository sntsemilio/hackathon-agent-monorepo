from __future__ import annotations

from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()
storage_uri = settings.rate_limit_storage_url or settings.redis_url
limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)


async def enforce_budget_limit(request: Request, identity: str) -> None:
    """Extra redis.asyncio-backed budget limiter layered on top of slowapi."""

    redis_client = request.app.state.redis_client
    window = request.app.state.settings.budget_window_seconds
    budget = request.app.state.settings.budget_limit_per_window
    key = f"budget:{identity}:{window}"

    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, window)

    if count > budget:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Token budget rate limit exceeded.",
        )


def rate_limit_exceeded_handler(_: Request, exc: RateLimitExceeded):
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded: {exc.detail}",
    )
