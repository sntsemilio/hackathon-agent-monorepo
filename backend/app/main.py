"""
backend/app/main.py
====================

Bootstrap del FastAPI app del agente Havi.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.api.routes import router as chat_router, admin_router, lifespan
from app.api.ws import router as ws_router
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

    # FastAPI OTel instrumentation
    if settings.OTEL_ENABLED:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
            logging.getLogger(__name__).info("FastAPI OTel instrumentation enabled")
        except ImportError:
            logging.getLogger(__name__).warning(
                "opentelemetry-instrumentation-fastapi not available"
            )

    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(ws_router)

    @app.get("/api/health")
    async def root():
        return {"service": "havi", "version": "1.0.0", "ok": True}

    # Mount frontend static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            # Resolve to index.html for React Router compatibility, or serve static files
            path = os.path.abspath(os.path.join(static_dir, full_path))
            if not path.startswith(os.path.abspath(static_dir)):
                return FileResponse(os.path.join(static_dir, "index.html"))
            if os.path.isfile(path):
                return FileResponse(path)
            return FileResponse(os.path.join(static_dir, "index.html"))

    return app


app = create_app()
