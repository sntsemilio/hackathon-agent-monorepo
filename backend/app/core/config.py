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
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "Hackathon Agent API"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    TESTING: bool = False
    CORS_ALLOW_ORIGINS: str = "*"

    # Security / auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ADMIN_ROLE_NAME: str = "admin"
    SECURITY_VIOLATION_MESSAGE: str = (
        "Security policy violation detected. The request was blocked by the guardrail."
    )

    # Infra / redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_INDEX_NAME: str = "hackathon_docs"
    REDIS_PREFIX: str = "doc:"
    REDIS_VECTOR_DIMS: int = 1536
    FICHA_PREFIX: str = "ficha:"
    FICHA_TTL_SECONDS: int = 0
    CONVERSATIONAL_PROFILE_PREFIX: str = "conv_profile:"
    RATE_LIMIT_STORAGE_URL: str = ""
    CHAT_RATE_LIMIT: str = "20/minute"
    BUDGET_LIMIT_PER_WINDOW: int = 20
    BUDGET_WINDOW_SECONDS: int = 60

    # Analytics / ML
    ANALYTICS_MODELS_DIR: Path = Path("app/analytics/models")

    # LLMs (LiteLLM router)
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_API_BASE: str = "http://localhost:11434"
    GUARDRAIL_MODEL: str = "gpt-4o-mini"
    SUMMARIZER_MODEL: str = "gpt-4o-mini"
    PROFILER_MODEL: str = "gpt-4o-mini"
    SUPERVISOR_ROUTER_MODEL: str = "gpt-4o-mini"
    LITELLM_MODEL_PROFILER: str = "anthropic/claude-haiku-4-5"
    LITELLM_MODEL_PLANNER: str = "anthropic/claude-haiku-4-5"
    LITELLM_MODEL_RESPONDER: str = "anthropic/claude-sonnet-4-6"
    LITELLM_MODEL_GUARDRAIL: str = "anthropic/claude-haiku-4-5"
    LITELLM_MODEL_SUMMARIZER: str = "anthropic/claude-haiku-4-5"
    LITELLM_TEMPERATURE: float = 0.0
    LLM_FALLBACK_INPUT_COST_PER_1K: float = 0.001
    LLM_FALLBACK_OUTPUT_COST_PER_1K: float = 0.003

    # RAG
    RAG_DENSE_TOP_K: int = 15
    RAG_FINAL_TOP_K: int = 3
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBED_DIM: int = 384

    # Agent graph
    MAX_GLOBAL_ITERATIONS: int = 5

    # MCP connectivity
    MCP_HOST: str = "localhost"
    MCP_PORT: int = 8765
    MCP_CONNECT_TIMEOUT_SECONDS: int = 5

    # Observability
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "havi-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_OTLP_HEADERS: str = ""
    OBS_HISTORY_LIMIT: int = 200
    OBS_SSE_TRACE_EVENTS: bool = True

    # Eval harness
    REGRESSION_BASE_URL: str = "http://localhost:8080"

    # MCP Gateway
    MCP_GATEWAY_URL: str = "http://localhost:8765"
    MCP_GATEWAY_TOKEN: str = "demo-token"

    # WebSocket
    WS_PROACTIVE_INTERVAL_SECONDS: int = 30

    # Feature flags
    FEATURE_FLAGS_REDIS_KEY: str = "feature_flags"

    # Legacy aliases used by older modules
    @property
    def MODELS_DIR(self) -> Path:
        return self.ANALYTICS_MODELS_DIR

    @property
    def testing(self) -> bool:
        return self.TESTING

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    @property
    def redis_index_name(self) -> str:
        return self.REDIS_INDEX_NAME

    @property
    def redis_prefix(self) -> str:
        return self.REDIS_PREFIX

    @property
    def redis_vector_dims(self) -> int:
        return self.REDIS_VECTOR_DIMS

    @property
    def rate_limit_storage_url(self) -> str:
        return self.RATE_LIMIT_STORAGE_URL

    @property
    def budget_window_seconds(self) -> int:
        return self.BUDGET_WINDOW_SECONDS

    @property
    def budget_limit_per_window(self) -> int:
        return self.BUDGET_LIMIT_PER_WINDOW

    @property
    def rag_dense_top_k(self) -> int:
        return self.RAG_DENSE_TOP_K

    @property
    def rag_final_top_k(self) -> int:
        return self.RAG_FINAL_TOP_K

    @property
    def jwt_secret_key(self) -> str:
        return self.JWT_SECRET_KEY

    @property
    def jwt_algorithm(self) -> str:
        return self.JWT_ALGORITHM

    @property
    def admin_role_name(self) -> str:
        return self.ADMIN_ROLE_NAME


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
