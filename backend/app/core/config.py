from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hackathon Agent API"
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8080
    testing: bool = False

    jwt_secret_key: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    admin_role_name: str = "admin"

    guardrail_model: str = "gpt-4o-mini"
    summarizer_model: str = "gpt-4o-mini"
    profiler_model: str = "gpt-4o-mini"
    supervisor_router_model: str = "gpt-4o-mini"
    litellm_temperature: float = 0.0
    security_violation_message: str = (
        "Security policy violation detected. The request was blocked by the guardrail."
    )

    redis_url: str = "redis://redis:6379/0"
    redis_index_name: str = "hackathon_docs"
    redis_prefix: str = "doc:"
    redis_vector_dims: int = 1536
    rate_limit_storage_url: str | None = None
    chat_rate_limit: str = "20/minute"
    budget_limit_per_window: int = 20
    budget_window_seconds: int = 60
    conversational_profile_prefix: str = "conv_profile:"

    analytics_models_dir: str = "app/analytics/models"

    mcp_host: str = "localhost"
    mcp_port: int = 8765
    mcp_connect_timeout_seconds: float = 5.0

    max_global_iterations: int = 5

    rag_dense_top_k: int = 15
    rag_final_top_k: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
