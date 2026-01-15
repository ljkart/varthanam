"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Configuration for the FastAPI application."""

    app_name: str
    environment: str
    log_level: str


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
    )
