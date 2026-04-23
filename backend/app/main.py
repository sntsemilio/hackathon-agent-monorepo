from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agents.supervisor import build_supervisor_graph
from app.core.checkpointer import close_checkpointer, create_checkpointer
from app.core.config import get_settings
from app.core.database import create_redis_client, verify_redis_connection
from app.rag.vector_store import RedisHybridVectorStore


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str | None = None


def _message_to_text(message: Any) -> str:
    if isinstance(message, BaseMessage):
        content = message.content
    elif isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = message

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    return str(content)


def _extract_final_response(output_state: dict[str, Any], fallback: str = "") -> str:
    final_response = output_state.get("final_response")
    if isinstance(final_response, str) and final_response.strip():
        return final_response

    messages = output_state.get("messages", [])
    if isinstance(messages, list):
        for message in reversed(messages):
            text = _message_to_text(message).strip()
            if text:
                return text
    return fallback


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, BaseMessage):
        return {
            "type": value.type,
            "content": _message_to_text(value),
        }
    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    redis_client = create_redis_client(settings)
    if not await verify_redis_connection(redis_client):
        raise RuntimeError("Unable to connect to Redis during startup")

    vector_store = RedisHybridVectorStore(
        redis_url=settings.redis_url,
        index_name=settings.redis_index_name,
        prefix=settings.redis_prefix,
        vector_dims=settings.redis_vector_dims,
    )
    await vector_store.initialize()

    checkpointer, checkpointer_context = await create_checkpointer(settings)
    graph = build_supervisor_graph(checkpointer=checkpointer)

    app.state.settings = settings
    app.state.redis_client = redis_client
    app.state.vector_store = vector_store
    app.state.checkpointer = checkpointer
    app.state.checkpointer_context = checkpointer_context
    app.state.graph = graph

    try:
        yield
    finally:
        await redis_client.aclose()
        await close_checkpointer(checkpointer, checkpointer_context)


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, Any]:
    redis_ok = await verify_redis_connection(app.state.redis_client)
    return {
        "status": "ok" if redis_ok else "degraded",
        "environment": app.state.settings.environment,
        "redis": redis_ok,
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest) -> EventSourceResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message must not be blank")

    thread_id = request.thread_id or str(uuid4())
    initial_state = {
        "messages": [HumanMessage(content=message)],
        "thread_id": thread_id,
        "global_iterations": 0,
    }
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator():
        final_response = ""
        try:
            async for event in app.state.graph.astream_events(
                initial_state,
                config=config,
                version="v2",
            ):
                data = event.get("data", {})
                if isinstance(data, dict):
                    output = data.get("output")
                    if isinstance(output, dict):
                        final_response = _extract_final_response(output, fallback=final_response)

                payload = {
                    "event": event.get("event", "unknown"),
                    "name": event.get("name", "anonymous"),
                    "data": _to_json_safe(data),
                }
                yield {
                    "event": "trace",
                    "data": json.dumps(payload, ensure_ascii=True),
                }

        except Exception as exc:
            error_payload = {
                "thread_id": thread_id,
                "error": str(exc),
            }
            yield {
                "event": "error",
                "data": json.dumps(error_payload, ensure_ascii=True),
            }
            return

        if not final_response:
            final_response = "Graph execution completed without a captured final response."

        yield {
            "event": "final",
            "data": json.dumps(
                {
                    "thread_id": thread_id,
                    "response": final_response,
                },
                ensure_ascii=True,
            ),
        }

    return EventSourceResponse(event_generator(), media_type="text/event-stream")
