from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agents.micro_agents.profiler_slm import update_conversational_profile
from app.core.config import get_settings
from app.core.database import get_conversational_profile, set_conversational_profile
from app.core.rate_limit import enforce_budget_limit, limiter

router = APIRouter(tags=["chat"])
settings = get_settings()


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str | None = None
    user_id: str | None = Field(default=None, min_length=1)
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


async def _persist_profile_after_stream(
    user_id: str,
    existing_profile: dict[str, Any],
    stream_snapshot: dict[str, Any],
) -> None:
    """Persist profile updates after SSE stream completion."""

    if stream_snapshot.get("stream_error"):
        return

    candidate_messages = [
        str(stream_snapshot.get("user_message", "")).strip(),
        str(stream_snapshot.get("assistant_message", "")).strip(),
    ]
    new_messages = [message for message in candidate_messages if message]
    if not new_messages:
        return

    try:
        updated_profile = await update_conversational_profile(
            current_profile=existing_profile,
            new_messages=new_messages,
        )
        await set_conversational_profile(user_id=user_id, profile_data=updated_profile)
    except (OSError, RuntimeError, TypeError, ValueError):
        # Never fail the request lifecycle because of post-stream profile persistence.
        return


@router.post("/chat/stream")
@limiter.limit(settings.chat_rate_limit)
async def chat_stream(
    request: Request,
    payload: ChatStreamRequest,
    background_tasks: BackgroundTasks,
) -> EventSourceResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message must not be blank")

    thread_id = payload.thread_id or str(uuid4())
    user_id = payload.user_id.strip() if payload.user_id else thread_id
    identity = f"{request.client.host if request.client else 'unknown'}:{thread_id}"
    await enforce_budget_limit(request, identity)

    analytics_engine = getattr(request.app.state, "analytics_engine", None)
    analytics_task = (
        analytics_engine.get_user_insights(user_id)
        if analytics_engine is not None
        else asyncio.sleep(0, result={})
    )

    analytics_result, conversational_result = await asyncio.gather(
        analytics_task,
        get_conversational_profile(user_id),
        return_exceptions=True,
    )

    analytics_insights = analytics_result if isinstance(analytics_result, dict) else {}
    conversational_profile = (
        conversational_result if isinstance(conversational_result, dict) else {}
    )
    user_persona = {
        "user_id": user_id,
        "analytics_insights": analytics_insights,
        "conversational_profile": conversational_profile,
    }

    initial_state = {
        "messages": [HumanMessage(content=message)],
        "thread_id": thread_id,
        "global_iterations": 0,
        "active_team": "guardrail",
        "user_persona": user_persona,
        "base64_images": payload.base64_images or [],
        "delegation_trace": [],
    }
    config = {"configurable": {"thread_id": thread_id}}
    stream_snapshot: dict[str, Any] = {
        "user_message": message,
        "assistant_message": "",
        "stream_error": False,
    }

    async def event_generator():
        final_response = ""
        latest_output: dict[str, Any] = {}

        try:
            async for output in request.app.state.graph.astream(
                initial_state,
                config=config,
            ):
                if isinstance(output, dict):
                    latest_output = output
                    final_response = _extract_final_response(output, fallback=final_response)

                payload_data = {
                    "event": "state_update",
                    "name": "graph.astream",
                    "data": _to_json_safe(output),
                }
                yield {
                    "event": "trace",
                    "data": json.dumps(payload_data, ensure_ascii=True),
                }

        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            stream_snapshot["stream_error"] = True
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
        stream_snapshot["assistant_message"] = final_response

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

    background_tasks.add_task(
        _persist_profile_after_stream,
        user_id,
        conversational_profile,
        stream_snapshot,
    )

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        background=background_tasks,
    )
