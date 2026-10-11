from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "production"] = "development"
    database_url: SecretStr = SecretStr("sqlite+pysqlite:///./data/ai_agent.db")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    model_provider: str | None = None
    model_name: str | None = None
    model_api_key: SecretStr | None = None
    model_base_url: str | None = None

    @model_validator(mode="after")
    def validate_database(self) -> Self:
        try:
            url = make_url(self.database_url.get_secret_value())
        except ArgumentError:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL") from None

        if self.app_env == "development":
            if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
                raise ValueError("Development requires a SQLite DATABASE_URL")
            if url.query:
                raise ValueError("Use a plain SQLite file URL without query parameters")
        else:
            if url.drivername != "postgresql+psycopg":
                raise ValueError("Production requires a postgresql+psycopg DATABASE_URL")
            if not url.database:
                raise ValueError("Production DATABASE_URL must include a database name")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
