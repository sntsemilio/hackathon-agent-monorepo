from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.core.config import get_settings
from app.core.rate_limit import enforce_budget_limit, limiter

router = APIRouter(tags=["chat"])
settings = get_settings()


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str | None = None
    base64_images: list[str] | None = None


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


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    # Lightweight approximation to monitor budget trends in the admin panel.
    return max(1, len(text) // 4)


@router.post("/chat/stream")
@limiter.limit(settings.chat_rate_limit)
async def chat_stream(request: Request, payload: ChatStreamRequest) -> EventSourceResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message must not be blank")

    thread_id = payload.thread_id or str(uuid4())
    identity = f"{request.client.host if request.client else 'unknown'}:{thread_id}"
    await enforce_budget_limit(request, identity)

    initial_state = {
        "messages": [HumanMessage(content=message)],
        "thread_id": thread_id,
        "global_iterations": 0,
        "active_team": "guardrail",
        "base64_images": payload.base64_images or [],
        "delegation_trace": [],
    }
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator():
        final_response = ""
        latest_output: dict[str, Any] = {}

        try:
            async for event in request.app.state.graph.astream_events(
                initial_state,
                config=config,
                version="v2",
            ):
                data = event.get("data", {})
                if isinstance(data, dict):
                    output = data.get("output")
                    if isinstance(output, dict):
                        latest_output = output
                        final_response = _extract_final_response(output, fallback=final_response)

                payload_data = {
                    "event": event.get("event", "unknown"),
                    "name": event.get("name", "anonymous"),
                    "data": _to_json_safe(data),
                }
                yield {
                    "event": "trace",
                    "data": json.dumps(payload_data, ensure_ascii=True),
                }

        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "thread_id": thread_id,
                        "error": str(exc),
                    },
                    ensure_ascii=True,
                ),
            }
            return

        if not final_response:
            final_response = "Graph execution completed without a captured final response."

        runtime_metrics = request.app.state.runtime_metrics
        runtime_metrics["requests_total"] += 1
        runtime_metrics["token_usage_total"] += _estimate_tokens(message) + _estimate_tokens(final_response)

        trace = latest_output.get("delegation_trace", [])
        if isinstance(trace, list):
            runtime_metrics["delegation_traces"].append(trace)
            runtime_metrics["delegation_traces"] = runtime_metrics["delegation_traces"][-100:]

        rag_metrics = latest_output.get("rag_metrics", {})
        if isinstance(rag_metrics, dict) and rag_metrics:
            runtime_metrics["rag_metrics_history"].append(rag_metrics)
            runtime_metrics["rag_metrics_history"] = runtime_metrics["rag_metrics_history"][-100:]

        yield {
            "event": "final",
            "data": json.dumps(
                {
                    "thread_id": thread_id,
                    "response": final_response,
                    "delegation_trace": trace,
                    "rag_metrics": rag_metrics,
                },
                ensure_ascii=True,
            ),
        }

    return EventSourceResponse(event_generator(), media_type="text/event-stream")
