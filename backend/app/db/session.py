"""SQLAlchemy engine and session helpers.

This module centralizes engine creation so the rest of the application can stay
agnostic about database configuration details and focus on business logic.
"""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import Settings, get_app_settings


@lru_cache(maxsize=1)
def get_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the provided database URL.

    Args:
        database_url: SQLAlchemy database URL.

    Returns:
        Engine: SQLAlchemy engine configured for the given database URL.
    """
    return create_engine(database_url, future=True)


def get_session_factory(settings: Settings) -> sessionmaker[Session]:
    """Build a session factory bound to the configured engine.

    Args:
        settings: Application settings with the database URL.

    Returns:
        sessionmaker[Session]: Factory for creating new database sessions.
    """
    return sessionmaker(
        bind=get_engine(settings.database_url),
        autoflush=False,
        autocommit=False,
    )


def get_db_session(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> Generator[Session, None, None]:
    """Provide a database session dependency for FastAPI.

    Args:
        settings: Application settings to build the session factory.

    Yields:
        Session: SQLAlchemy session scoped to the caller.
    """
    session_factory = get_session_factory(settings)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
