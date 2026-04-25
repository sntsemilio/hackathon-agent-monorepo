from __future__ import annotations

import inspect
from typing import Any

from app.core.config import Settings

try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    MemorySaver = None  # type: ignore[assignment]

try:
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver
except ImportError:
    try:
        from langgraph.checkpoint.redis import AsyncRedisSaver
    except ImportError:
        AsyncRedisSaver = None  # type: ignore[assignment]


class CheckpointerUnavailableError(RuntimeError):
    """Raised when the Redis checkpointer package is not available."""


async def create_checkpointer(settings: Settings) -> tuple[Any, Any | None]:
    if settings.testing:
        if MemorySaver is None:
            return None, None
        return MemorySaver(), None

    if AsyncRedisSaver is None:
        if MemorySaver is None:
            raise CheckpointerUnavailableError(
                "AsyncRedisSaver is unavailable. Install langgraph-checkpoint-redis."
            )
        return MemorySaver(), None

    if hasattr(AsyncRedisSaver, "from_conn_string"):
        saver_candidate = AsyncRedisSaver.from_conn_string(settings.redis_url)
    else:
        saver_candidate = AsyncRedisSaver(settings.redis_url)

    if inspect.isawaitable(saver_candidate):
        saver_candidate = await saver_candidate

    if hasattr(saver_candidate, "__aenter__") and hasattr(saver_candidate, "__aexit__"):
        saver = await saver_candidate.__aenter__()
        return saver, saver_candidate

    return saver_candidate, None


async def close_checkpointer(saver: Any, saver_context: Any | None = None) -> None:
    if saver is None:
        return

    if saver_context is not None:
        await saver_context.__aexit__(None, None, None)
        return

    close_method = getattr(saver, "aclose", None)
    if callable(close_method):
        maybe_coro = close_method()
        if inspect.isawaitable(maybe_coro):
            await maybe_coro
