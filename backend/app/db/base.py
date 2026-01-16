"""Shared declarative base for SQLAlchemy models.

Keeping the Base in a single module makes Alembic metadata discovery reliable
without importing application services or routers.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
