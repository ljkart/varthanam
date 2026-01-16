"""Tests for standardized API error handling."""

from __future__ import annotations

from collections.abc import Iterator

from app.core.settings import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.services.auth import get_current_user
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def create_test_app() -> FastAPI:
    """Create a FastAPI app with an isolated in-memory database."""
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    settings = Settings(
        app_name="Varthanam Test API",
        environment="test",
        log_level="INFO",
        database_url="sqlite+pysqlite://",
        jwt_secret_key="test-secret",
        jwt_access_token_expire_minutes=60,
    )
    app = create_app(settings=settings)

    def override_get_db_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    return app


def test_validation_error_returns_standard_response() -> None:
    """Validation errors should map to the standard error schema."""
    client = TestClient(create_test_app())

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid@example.com"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error_code"] == "validation_error"
    assert payload["message"]
    assert isinstance(payload["details"], list)


def test_http_exception_returns_standard_response() -> None:
    """Explicit HTTPException responses should use the standard error schema."""
    client = TestClient(create_test_app())

    client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "secure-password"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["error_code"] == "http_error"
    assert payload["message"] == "Invalid email or password."
    assert payload["details"] is None


def test_unhandled_exception_returns_safe_500() -> None:
    """Unhandled exceptions should return a safe 500 response."""
    app = create_test_app()

    def override_current_user() -> None:
        raise RuntimeError("boom")

    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 500
    payload = response.json()
    assert payload["error_code"] == "internal_server_error"
    assert payload["message"]
    assert payload["details"] is None
