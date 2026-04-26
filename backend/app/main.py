"""
backend/app/main.py
====================

Bootstrap del FastAPI app del agente Havi.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as chat_router, lifespan
from app.api.admin import router as admin_router
from app.api.users import router as users_router
from app.core.config import get_settings


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title="Hey Banco · Agente Havi",
        version="1.0.0",
        description="Agente conversacional con personalización por clustering.",
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(users_router)

    @app.get("/")
    async def root():
        return {"service": "havi", "version": "1.0.0", "ok": True}

    return app


app = create_app()
