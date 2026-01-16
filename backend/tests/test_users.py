"""Tests for the User model and password utilities."""

import pytest
from app.core.security import get_password_hash, verify_password
from app.db.base import Base
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


def create_test_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_user_can_be_created_and_persisted() -> None:
    """User records should persist with expected fields."""
    session = create_test_session()
    try:
        user = User(email="user@example.com", password_hash="hashed", is_active=True)
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        assert user.email == "user@example.com"
    finally:
        session.close()


def test_user_email_is_unique() -> None:
    """Email uniqueness should be enforced at the database level."""
    session = create_test_session()
    try:
        session.add(
            User(email="unique@example.com", password_hash="hash", is_active=True)
        )
        session.commit()

        session.add(
            User(email="unique@example.com", password_hash="hash2", is_active=True)
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_password_hashing_verification() -> None:
    """Password hashes should verify correctly and reject invalid passwords."""
    password = "super-secret"

    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong-password", hashed_password) is False
