from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.agents.supervisor import build_supervisor_graph
from app.api.admin.evals import router as admin_evals_router
from app.api.admin.metrics import router as admin_metrics_router
from app.api.routes import router as chat_router
from app.core.checkpointer import close_checkpointer, create_checkpointer
from app.core.config import get_settings
from app.core.database import create_redis_client, verify_redis_connection
from app.core.rate_limit import limiter
from app.evals.framework import RagasEvaluationRunner
from app.rag.vector_store import RedisHybridVectorStore


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()

    redis_client = create_redis_client(settings)
    redis_ok = await verify_redis_connection(redis_client)
    if not redis_ok and not settings.testing:
        raise RuntimeError("Unable to connect to Redis during startup")

    vector_store: RedisHybridVectorStore | None = None
    if not settings.testing:
        try:
            vector_store = RedisHybridVectorStore(
                redis_url=settings.redis_url,
                index_name=settings.redis_index_name,
                prefix=settings.redis_prefix,
                vector_dims=settings.redis_vector_dims,
            )
            await vector_store.initialize()
        except (ImportError, OSError, RuntimeError, TypeError, ValueError):
            # Continue in degraded mode when RedisVL is not available.
            vector_store = None

    checkpointer, checkpointer_context = await create_checkpointer(settings)
    graph = build_supervisor_graph(checkpointer=checkpointer)

    application.state.settings = settings
    application.state.redis_client = redis_client
    application.state.vector_store = vector_store
    application.state.checkpointer = checkpointer
    application.state.checkpointer_context = checkpointer_context
    application.state.graph = graph
    application.state.evals_runner = RagasEvaluationRunner()
    application.state.runtime_metrics = {
        "requests_total": 0,
        "token_usage_total": 0,
        "delegation_traces": [],
        "rag_metrics_history": [],
    }

    try:
        yield
    finally:
        if vector_store is not None:
            await vector_store.close()
        await redis_client.aclose()
        await close_checkpointer(checkpointer, checkpointer_context)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)

    application.include_router(chat_router)
    application.include_router(admin_metrics_router)
    application.include_router(admin_evals_router)

    @application.get("/health")
    async def health() -> dict[str, Any]:
        redis_ok = await verify_redis_connection(application.state.redis_client)
        return {
            "status": "ok" if redis_ok else "degraded",
            "environment": application.state.settings.environment,
            "redis": redis_ok,
        }

    return application


app = create_app()
