from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

# Ensure settings are configured before importing application modules.
os.environ["TESTING"] = "true"
os.environ["RATE_LIMIT_STORAGE_URL"] = "memory://"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session", autouse=True)
def set_test_env() -> None:
    get_settings.cache_clear()


@pytest.fixture
async def app():
    get_settings.cache_clear()
    return create_app()


@pytest.fixture
async def async_client(app) -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client


@pytest.fixture
def admin_token() -> str:
    return jwt.encode({"sub": "admin-user", "role": "admin"}, "test-secret", algorithm="HS256")


@pytest.fixture
def user_token() -> str:
    return jwt.encode({"sub": "regular-user", "role": "viewer"}, "test-secret", algorithm="HS256")
