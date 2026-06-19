"""
core/config.py

Single source of truth for all application configuration.
Reads from environment variables / .env file.
Validates types and required fields at startup — if something
is missing or wrong, the app fails immediately with a clear
error rather than crashing later in a confusing way.

Usage anywhere in the app:
    from core.config import settings
    print(settings.anthropic_model)
    print(settings.postgres_url)
"""

from functools import lru_cache
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    Pydantic Settings automatically reads values from:
    1. Environment variables (highest priority)
    2. .env file
    3. Default values defined here (lowest priority)

    Field names must match the variable names in .env
    (case-insensitive by default).
    """

    model_config = SettingsConfigDict(
    env_file=str(Path(__file__).parent.parent.parent / ".env"),
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
    )

    # ─────────────────────────────────────────
    # App
    # ─────────────────────────────────────────
    app_env: str = Field(default="development")
    app_name: str = Field(default="ai-data-agent")
    app_version: str = Field(default="0.1.0")

    # ─────────────────────────────────────────
    # PostgreSQL — individual fields
    # We build the connection URLs as computed
    # fields so the app never needs to construct
    # them manually
    # ─────────────────────────────────────────
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_readonly_user: str
    postgres_readonly_password: str

    # ─────────────────────────────────────────
    # Redis
    # ─────────────────────────────────────────
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: str
    redis_cache_ttl: int = Field(default=3600)

    # ─────────────────────────────────────────
    # OpenAI
    # ─────────────────────────────────────────
    openai_api_key: str
    openai_model: str = Field(default="gpt-4o")
    openai_max_tokens: int = Field(default=4096)

    # ─────────────────────────────────────────
    # Security
    # ─────────────────────────────────────────
    secret_key: str
    rate_limit_per_minute: int = Field(default=20)
    max_rows_per_query: int = Field(default=1000)

    # ─────────────────────────────────────────
    # pgAdmin (dev only — harmless in prod
    # since pgadmin container won't run)
    # ─────────────────────────────────────────
    pgadmin_email: str = Field(default="admin@local.dev")
    pgadmin_password: str = Field(default="admin")

    # ─────────────────────────────────────────
    # Computed fields — built from raw fields
    # above, never set directly in .env
    # ─────────────────────────────────────────

    @computed_field
    @property
    def postgres_url(self) -> str:
        """
        Full admin connection URL for running migrations
        and schema setup. Never used by the AI agent.
        """
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def postgres_readonly_url(self) -> str:
        """
        Read-only connection URL used by the AI agent
        for all user-triggered queries. This user has
        SELECT permission only — cannot modify data.
        """
        return (
            f"postgresql+asyncpg://{self.postgres_readonly_user}:"
            f"{self.postgres_readonly_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        """Redis connection URL with password."""
        return (
            f"redis://:{self.redis_password}@"
            f"{self.redis_host}:{self.redis_port}/0"
        )

    # ─────────────────────────────────────────
    # Helper properties
    # ─────────────────────────────────────────

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# ─────────────────────────────────────────────────────────────
# @lru_cache means this function only runs ONCE no matter how
# many times it is called across the application.
# The Settings object is created once at startup and reused.
# This is the standard FastAPI pattern for settings.
# ─────────────────────────────────────────────────────────────
@lru_cache
def get_settings() -> Settings:
    return Settings()


# Convenience — import this directly anywhere in the app
# from core.config import settings
settings = get_settings()