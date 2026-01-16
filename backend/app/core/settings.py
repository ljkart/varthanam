"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Request


@dataclass(frozen=True)
class Settings:
    """Configuration for the FastAPI application."""

    app_name: str
    environment: str
    log_level: str
    database_url: str
    jwt_secret: str
    jwt_access_token_exp_minutes: int


@lru_cache
def get_settings() -> Settings:
    """Resolve settings from the environment.

    Returns:
        Settings: The resolved configuration values.
    """
    # Keep env parsing minimal until the config surface area grows.
    return Settings(
        app_name=os.getenv("APP_NAME", "Varthanam API"),
        environment=os.getenv("APP_ENVIRONMENT", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        database_url=os.getenv("DATABASE_URL", "sqlite+pysqlite:///./varthanam.db"),
        jwt_secret=os.getenv("JWT_SECRET", "dev-secret"),
        jwt_access_token_exp_minutes=int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        ),
    )


def get_app_settings(request: Request) -> Settings:
    """Retrieve application settings from the FastAPI app state.

    Args:
        request: Incoming request used to access the app state.

    Returns:
        Settings: Settings instance configured for the application.
    """
    return request.app.state.settings
