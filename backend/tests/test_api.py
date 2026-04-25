from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health(async_client) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "redis" in payload


@pytest.mark.asyncio
async def test_chat_stream_emits_final_event(async_client) -> None:
    response = await async_client.post(
        "/chat/stream",
        json={"message": "What is hybrid search?", "thread_id": "api-thread-1"},
    )
    assert response.status_code == 200
    assert "event: final" in response.text
