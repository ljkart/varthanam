"""SQLAlchemy engine and session helpers.

This module centralizes engine creation so the rest of the application can stay
agnostic about database configuration details and focus on business logic.
"""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_engine(settings: Settings) -> Engine:
    """Create a SQLAlchemy engine from application settings.

    Args:
        settings: Application settings with the database URL.

    Returns:
        Engine: SQLAlchemy engine configured for the given database URL.
    """
    return create_engine(settings.database_url, future=True)


def get_session_factory(settings: Settings) -> sessionmaker[Session]:
    """Build a session factory bound to the configured engine.

    Args:
        settings: Application settings with the database URL.

    Returns:
        sessionmaker[Session]: Factory for creating new database sessions.
    """
    return sessionmaker(bind=get_engine(settings), autoflush=False, autocommit=False)


def get_db_session(settings: Settings | None = None) -> Generator[Session, None, None]:
    """Provide a database session dependency for FastAPI.

    Args:
        settings: Optional settings override for tests or alternate configs.

    Yields:
        Session: SQLAlchemy session scoped to the caller.
    """
    resolved_settings = settings or get_settings()
    session_factory = get_session_factory(resolved_settings)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
