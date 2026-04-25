"""
backend/app/api/routes.py
=========================

Endpoint principal del agente Havi.

CAMBIO PRINCIPAL (BLOQUEADOR 1 del documento de contexto):
    - El lifespan inicializa el cliente Redis y lo deja en `app.state.redis`.
    - El endpoint POST /chat/stream pasa ese cliente como `_redis_client`
      en el estado inicial del supervisor LangGraph para que `ficha_injector_node`
      pueda hacer `state.get("_redis_client")` correctamente.

Este archivo asume:
    - `app.agents.supervisor.build_graph()` devuelve el grafo LangGraph compilado.
    - `app.core.config.get_settings()` expone REDIS_URL, FICHA_PREFIX, FICHA_TTL_SECONDS.
    - `app.core.database.create_redis_client(url)` devuelve un cliente redis.asyncio.Redis.

Si tu repo usa otros nombres, ajusta los imports en la parte superior.
"""
from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agents.supervisor import build_graph
from app.core.config import get_settings
from app.core.database import create_redis_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: inicializa Redis y compila el grafo una sola vez
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan handler: arranca el cliente Redis y compila el supervisor.

    Deja en `app.state`:
        - app.state.redis        -> redis.asyncio.Redis client
        - app.state.graph        -> grafo LangGraph compilado
        - app.state.settings     -> Settings (env vars)
    """
    settings = get_settings()
    app.state.settings = settings

    redis_client = await create_redis_client(settings.REDIS_URL)
    app.state.redis = redis_client
    logger.info("Redis client initialized at %s", settings.REDIS_URL)

    app.state.graph = build_graph()
    logger.info("Supervisor graph compiled and ready")

    try:
        yield
    finally:
        try:
            await redis_client.aclose()
        except Exception:
            logger.exception("Error closing Redis client")
        logger.info("Lifespan shutdown complete")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatStreamRequest(BaseModel):
    """Payload de POST /chat/stream."""

    user_id: str = Field(..., description="ID del usuario en Hey Banco (p.ej. USR-00001)")
    message: str = Field(..., description="Mensaje del usuario")
    session_id: Optional[str] = Field(
        default=None,
        description="Identificador de sesión conversacional. Si no viene, se genera uno.",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadatos opcionales (canal, device, etc.)",
    )


def _build_initial_state(
    payload: ChatStreamRequest,
    redis_client: Any,
    settings: Any,
) -> Dict[str, Any]:
    """
    Construye el dict de input al supervisor LangGraph.

    Inyecta el cliente Redis bajo la clave `_redis_client` para que
    `ficha_injector_node` pueda recuperar la ficha del usuario.
    El prefijo `_` indica que es un campo de runtime (no se persiste).
    """
    session_id = payload.session_id or f"sess-{uuid.uuid4().hex[:12]}"
    return {
        # Inputs del usuario
        "user_id": payload.user_id,
        "session_id": session_id,
        "input_text": payload.message,
        "metadata": payload.metadata or {},

        # Personalización (FichaInjector lo llenará)
        "ficha_cliente": None,

        # Runtime: cliente Redis y settings (no se persisten en checkpoints)
        "_redis_client": redis_client,
        "_ficha_prefix": settings.FICHA_PREFIX,
        "_ficha_ttl_seconds": settings.FICHA_TTL_SECONDS,

        # Buffers que llenan los demás nodos
        "messages": [],
        "guardrail": None,
        "profile": None,
        "research_context": None,
        "tool_results": None,
        "draft_response": None,
        "final_response": None,
    }


async def _stream_graph(
    graph: Any,
    initial_state: Dict[str, Any],
) -> AsyncIterator[bytes]:
    """
    Itera el grafo en modo stream y emite eventos SSE.

    Cada evento se serializa como `data: <json>\\n\\n`. El cliente puede
    distinguir tipos por la clave `event` dentro del payload.
    """
    config = {
        "configurable": {
            "thread_id": initial_state["session_id"],
            "user_id": initial_state["user_id"],
        }
    }

    try:
        async for chunk in graph.astream(initial_state, config=config, stream_mode="updates"):
            for node_name, node_state in chunk.items():
                event = {
                    "event": "node_update",
                    "node": node_name,
                    "data": _safe_serializable(node_state),
                }
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")

        yield b"data: {\"event\": \"done\"}\n\n"
    except Exception as exc:
        logger.exception("Graph streaming failed")
        err = {"event": "error", "message": str(exc)}
        yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")


def _safe_serializable(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limpia campos que no deben viajar al cliente:
        - cualquier clave que empiece con `_` (runtime, p.ej. _redis_client)
        - objetos no serializables a JSON
    """
    if not isinstance(state, dict):
        return {"_": str(state)}

    cleaned: Dict[str, Any] = {}
    for k, v in state.items():
        if k.startswith("_"):
            continue
        try:
            json.dumps(v, ensure_ascii=False, default=str)
            cleaned[k] = v
        except TypeError:
            cleaned[k] = str(v)
    return cleaned


# ---------------------------------------------------------------------------
# Endpoint principal
# ---------------------------------------------------------------------------
@router.post("/stream")
async def chat_stream(payload: ChatStreamRequest, request: Request) -> StreamingResponse:
    """
    Endpoint conversacional con SSE. Personalizado vía ficha_cliente en Redis.

    Flujo:
        FichaInjector -> Guardrail -> Profiler -> Supervisor -> (Research|ToolOps) -> Summarizer
    """
    redis_client = getattr(request.app.state, "redis", None)
    graph = getattr(request.app.state, "graph", None)
    settings = getattr(request.app.state, "settings", None)

    if redis_client is None or graph is None or settings is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready: Redis o grafo aún no inicializados.",
        )

    initial_state = _build_initial_state(payload, redis_client, settings)
    logger.info(
        "chat/stream user_id=%s session_id=%s",
        initial_state["user_id"],
        initial_state["session_id"],
    )

    return StreamingResponse(
        _stream_graph(graph, initial_state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Healthcheck para K8s / probes
# ---------------------------------------------------------------------------
@router.get("/healthz")
async def healthz(request: Request) -> Dict[str, Any]:
    redis_client = getattr(request.app.state, "redis", None)
    redis_ok = False
    if redis_client is not None:
        try:
            pong = await redis_client.ping()
            redis_ok = bool(pong)
        except Exception:
            redis_ok = False
    return {
        "ok": redis_ok and getattr(request.app.state, "graph", None) is not None,
        "redis": redis_ok,
        "graph_loaded": getattr(request.app.state, "graph", None) is not None,
    }
