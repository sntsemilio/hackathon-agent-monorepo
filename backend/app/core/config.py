from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hackathon Agent API"
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8080

    redis_url: str = "redis://redis:6379/0"
    redis_index_name: str = "hackathon_docs"
    redis_prefix: str = "doc:"
    redis_vector_dims: int = 1536

    mcp_host: str = "localhost"
    mcp_port: int = 8765
    mcp_connect_timeout_seconds: float = 5.0

    max_global_iterations: int = 6

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
