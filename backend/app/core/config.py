"""
backend/app/core/config.py
==========================

Settings basados en pydantic-settings. Lee env vars y .env.

Vars clave:
  REDIS_URL                  redis://localhost:6379
  FICHA_PREFIX               ficha:
  FICHA_TTL_SECONDS          0   (0 = sin expiración)
  MODELS_DIR                 ./backend/app/analytics/models
  ANTHROPIC_API_KEY          ...
  LITELLM_MODEL_PROFILER     anthropic/claude-haiku-4-5
  LITELLM_MODEL_PLANNER      anthropic/claude-haiku-4-5
  LITELLM_MODEL_RESPONDER    anthropic/claude-sonnet-4-6
  LITELLM_MODEL_GUARDRAIL    anthropic/claude-haiku-4-5
  LITELLM_MODEL_SUMMARIZER   anthropic/claude-haiku-4-5
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Infra
    REDIS_URL: str = "redis://localhost:6379"
    FICHA_PREFIX: str = "ficha:"
    FICHA_TTL_SECONDS: int = 0
    MODELS_DIR: Path = Path("./backend/app/analytics/models")

    # LLMs (LiteLLM router)
    ANTHROPIC_API_KEY: str = ""
    LITELLM_MODEL_PROFILER: str = "anthropic/claude-haiku-4-5"
    LITELLM_MODEL_PLANNER: str = "anthropic/claude-haiku-4-5"
    LITELLM_MODEL_RESPONDER: str = "anthropic/claude-sonnet-4-6"
    LITELLM_MODEL_GUARDRAIL: str = "anthropic/claude-haiku-4-5"
    LITELLM_MODEL_SUMMARIZER: str = "anthropic/claude-haiku-4-5"

    # RAG
    REDIS_INDEX_NAME: str = "havi_kb"
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBED_DIM: int = 384

    # API
    CORS_ALLOW_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
