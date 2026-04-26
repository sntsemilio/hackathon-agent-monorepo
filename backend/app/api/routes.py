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
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agents.supervisor import build_graph
from app.agents.conversation_memory import (
    load_conversation_history, save_conversation_turn, format_history_for_prompt
)
from app.api.admin import record_request
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


async def _build_initial_state(
    payload: ChatStreamRequest,
    redis_client: Any,
    settings: Any,
) -> Dict[str, Any]:
    """
    Construye el dict de input al supervisor LangGraph.

    Inyecta el cliente Redis bajo la clave `_redis_client` para que
    `ficha_injector_node` pueda recuperar la ficha del usuario.
    El prefijo `_` indica que es un campo de runtime (no se persiste).

    CAMBIO: ahora carga el historial de conversación desde Redis y lo
    inyecta para que el profiler tenga contexto.
    """
    session_id = payload.session_id or f"sess-{uuid.uuid4().hex[:12]}"

    # Cargar historial de conversación
    history = await load_conversation_history(redis_client, payload.user_id)
    conversation_context = format_history_for_prompt(history)

    return {
        # Inputs del usuario
        "user_id": payload.user_id,
        "session_id": session_id,
        "input_text": payload.message,
        "metadata": payload.metadata or {},

        # Historial conversacional para contexto
        "conversation_history": history,
        "conversation_context": conversation_context,

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


def _derive_status_label(final_state: Dict[str, Any]) -> str:
    """
    Derive a human-readable status label from the final state.
    Used for observability metrics recording.
    """
    ficha = final_state.get("ficha_cliente", {})
    if not isinstance(ficha, dict):
        ficha = {}

    segmentos = ficha.get("segmentos", {})
    conductual = segmentos.get("conductual", {})
    conductual_name = conductual.get("name", "") if isinstance(conductual, dict) else ""

    sugerencias = ficha.get("sugerencias_candidatas", [])

    if conductual_name == "actividad_atipica_alerta":
        return "actividad atípica"

    if sugerencias and len(sugerencias) > 0:
        prod = sugerencias[0].replace("_", " ").title()
        return f"{prod} sugerido"

    if final_state.get("final_response"):
        return "ok"

    return "proceso completado"


async def _stream_graph(
    graph: Any,
    initial_state: Dict[str, Any],
    redis_client: Any,
) -> AsyncIterator[bytes]:
    """
    Itera el grafo en modo stream y emite eventos SSE.

    CAMBIO: ahora también guarda el historial conversacional después
    de que el grafo termina y registra métricas de la request.

    Emite en formato SSE estándar:
        event: trace
        data: {...json...}

        event: final
        data: {...json...}
    """
    config = {
        "configurable": {
            "thread_id": initial_state["session_id"],
            "user_id": initial_state["user_id"],
        }
    }

    final_state = {}
    start_time = time.monotonic()
    try:
        async for chunk in graph.astream(initial_state, config=config, stream_mode="updates"):
            # Guardar el estado actualizado
            for node_name, node_state in chunk.items():
                final_state.update(node_state)
                # Emitir como trace event (formato SSE estándar)
                metadata = _safe_serializable(node_state)
                yield f"event: trace\n".encode("utf-8")
                yield f"data: {json.dumps({'node': node_name, 'status': 'done', 'latency_ms': 0, 'metadata': metadata}, ensure_ascii=False)}\n\n".encode("utf-8")

        # Guardar el turno en el historial
        user_id = initial_state.get("user_id")
        user_message = initial_state.get("input_text", "")
        final_response = final_state.get("final_response", "")

        if user_id and redis_client:
            await save_conversation_turn(redis_client, user_id, user_message, final_response)

        # Record metrics before sending final response
        latency_ms = (time.monotonic() - start_time) * 1000
        success = bool(final_response)
        tokens = final_state.get("_token_count", 100)  # estimate if not available
        status_label = _derive_status_label(final_state)
        cost = tokens * 0.0000015  # approx cost for gpt-4o-mini per token

        record_request(
            success=success,
            tokens=tokens,
            latency_ms=latency_ms,
            user_id=user_id or "anonymous",
            query=user_message[:60] if user_message else ".",
            status_label=status_label,
            cost=cost,
        )

        # Emitir final response al terminar
        ficha = final_state.get("ficha_cliente")
        yield f"event: final\n".encode("utf-8")
        yield f"data: {json.dumps({'response': final_response or 'Proceso completado', 'ficha': ficha}, ensure_ascii=False)}\n\n".encode("utf-8")
    except Exception as exc:
        logger.exception("Graph streaming failed")
        # Record failure metrics
        latency_ms = (time.monotonic() - start_time) * 1000
        user_id = initial_state.get("user_id", "anonymous")
        record_request(
            success=False,
            tokens=0,
            latency_ms=latency_ms,
            user_id=user_id,
            query=initial_state.get("input_text", ".")[:60],
            status_label="error",
            cost=0,
        )
        yield f"event: error\n".encode("utf-8")
        yield f"data: {json.dumps({'detail': str(exc), 'message': str(exc)}, ensure_ascii=False)}\n\n".encode("utf-8")


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

    CAMBIO: ahora también carga el historial conversacional para que el profiler
    tenga contexto de los turnos anteriores.

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

    initial_state = await _build_initial_state(payload, redis_client, settings)
    logger.info(
        "chat/stream user_id=%s session_id=%s history_turns=%d",
        initial_state["user_id"],
        initial_state["session_id"],
        len(initial_state.get("conversation_history", [])),
    )

    return StreamingResponse(
        _stream_graph(graph, initial_state, redis_client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Nuevos endpoints para perfiles de clientes personalizados
# ---------------------------------------------------------------------------
@router.get("/profiles/{user_id}")
async def get_customer_profile(user_id: str, request: Request) -> Dict[str, Any]:
    """
    Obtiene el perfil personalizado de un cliente.

    Responde con:
        - scenario: tipo de interacción (restructuracion_pago, prestamo_disponible, etc)
        - action_type: tipo de acción recomendada
        - recommendation: texto de recomendación
        - credit_profile: datos crediticios
        - transaction_stats: estadísticas de transacciones
    """
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Redis not available")

    profile_key = f"profile:{user_id}"
    profile_data = await redis_client.get(profile_key)

    if profile_data is None:
        raise HTTPException(status_code=404, detail=f"Profile not found for user {user_id}")

    profile = json.loads(profile_data)
    logger.info(f"Retrieved profile for {user_id}: scenario={profile.get('scenario')}")
    return profile


@router.get("/scenarios")
async def get_scenarios(request: Request) -> Dict[str, Any]:
    """
    Lista todos los escenarios disponibles con sus clientes.
    """
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Redis not available")

    summary_data = await redis_client.get("profiles:summary")
    if summary_data is None:
        raise HTTPException(status_code=404, detail="No profiles loaded")

    summary = json.loads(summary_data)
    return summary


@router.get("/scenarios/{scenario}/sample")
async def get_scenario_sample(scenario: str, request: Request) -> Dict[str, Any]:
    """
    Obtiene un cliente de ejemplo para un escenario específico.

    Escenarios disponibles:
        - restructuracion_pago: Cliente con buen score pero problemas de pago
        - prestamo_disponible: Cliente bueno para oferta de préstamo
        - upsell_productos: Cliente promedio para upsell
        - educacion_financiera: Cliente nuevo que necesita educación
    """
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Redis not available")

    scenario_key = f"scenarios:{scenario}"
    users_data = await redis_client.get(scenario_key)

    if users_data is None:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario} not found")

    users = json.loads(users_data)
    if not users:
        raise HTTPException(status_code=404, detail=f"No users found for scenario {scenario}")

    # Obtener el primer usuario como muestra
    sample_user_id = users[0]
    profile_key = f"profile:{sample_user_id}"
    profile_data = await redis_client.get(profile_key)

    if profile_data is None:
        raise HTTPException(status_code=500, detail="Profile data corrupted")

    profile = json.loads(profile_data)
    logger.info(f"Returning sample for scenario {scenario}: {sample_user_id}")
    return profile


@router.get("/scenarios/{scenario}/all")
async def get_scenario_customers(scenario: str, request: Request) -> Dict[str, Any]:
    """
    Lista todos los clientes de un escenario específico.
    """
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Redis not available")

    scenario_key = f"scenarios:{scenario}"
    users_data = await redis_client.get(scenario_key)

    if users_data is None:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario} not found")

    users = json.loads(users_data)
    logger.info(f"Returning {len(users)} customers for scenario {scenario}")
    return {
        "scenario": scenario,
        "total_count": len(users),
        "user_ids": users[:20],  # Limitar a 20 para no sobrecargar
    }


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
