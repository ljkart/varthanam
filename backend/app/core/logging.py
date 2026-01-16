"""Logging configuration for the backend application."""

from __future__ import annotations

import logging

from app.core.settings import Settings


def configure_logging(settings: Settings) -> None:
    """Configure standard logging for the application.

    Args:
        settings: The application settings controlling log verbosity.
    """
    # Centralized logging keeps API and future workers consistent.
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
