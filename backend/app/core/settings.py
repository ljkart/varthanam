"""Application settings loaded from environment variables.

ENV controls environment-specific defaults. In test mode, the database URL
defaults to an in-memory SQLite database to keep tests deterministic.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from fastapi import Request
from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the FastAPI application.

    Attributes:
        app_name: Human-readable API name for documentation and logs.
        environment: Deployment environment (dev/test/prod).
        log_level: Logging verbosity for the application.
        database_url: SQLAlchemy database URL.
        jwt_secret_key: Secret key used to sign JWT access tokens.
        jwt_algorithm: JWT signing algorithm, defaulting to HS256.
        jwt_access_token_expire_minutes: Access token lifetime in minutes.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(
        default="Varthanam API",
        validation_alias=AliasChoices("APP_NAME"),
        description="Display name for the API.",
    )
    environment: Literal["dev", "test", "prod"] = Field(
        validation_alias=AliasChoices("ENV", "APP_ENVIRONMENT"),
        description="Deployment environment: dev, test, or prod.",
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL"),
        description="Logging verbosity for the application.",
    )
    database_url: str = Field(
        validation_alias=AliasChoices("DATABASE_URL"),
        description="SQLAlchemy database URL.",
    )
    jwt_secret_key: SecretStr = Field(
        validation_alias=AliasChoices("JWT_SECRET_KEY", "JWT_SECRET"),
        description="Secret key for signing JWT access tokens.",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        min_length=1,
        validation_alias=AliasChoices("JWT_ALGORITHM"),
        description="JWT signing algorithm.",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        validation_alias=AliasChoices("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"),
        description="Access token lifetime in minutes.",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        """Normalize environment values to dev/test/prod."""
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        if normalized in {"development", "dev"}:
            return "dev"
        if normalized in {"production", "prod"}:
            return "prod"
        return normalized

    @model_validator(mode="before")
    @classmethod
    def apply_test_defaults(cls, values: dict[str, object]) -> dict[str, object]:
        """Apply test defaults to keep tests deterministic."""
        if not isinstance(values, dict):
            return values
        env_value = (
            values.get("ENV")
            or values.get("environment")
            or values.get("APP_ENVIRONMENT")
        )
        env = env_value.strip().lower() if isinstance(env_value, str) else env_value
        if env == "test" and not (
            values.get("DATABASE_URL") or values.get("database_url")
        ):
            values["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
        return values


@lru_cache
def get_settings() -> Settings:
    """Resolve settings from the environment.

    Returns:
        Settings: The resolved configuration values.
    """
    return Settings()


def get_app_settings(request: Request) -> Settings:
    """Retrieve application settings from the FastAPI app state.

    Args:
        request: Incoming request used to access the app state.

    Returns:
        Settings: Settings instance configured for the application.
    """
    return request.app.state.settings
