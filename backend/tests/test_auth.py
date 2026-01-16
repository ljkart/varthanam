"""Tests for authentication endpoints and JWT protection."""

from app.core.settings import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def create_test_client() -> TestClient:
    """Create a TestClient with an isolated in-memory database."""
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
        jwt_secret="test-secret",
        jwt_access_token_exp_minutes=60,
    )
    app = create_app(settings=settings)

    def override_get_db_session() -> Session:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    return TestClient(app)


def test_register_success_returns_user() -> None:
    """Registering a new user should return safe user fields."""
    client = create_test_client()

    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "secure-password"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == "user@example.com"
    assert "id" in payload
    assert "password_hash" not in payload


def test_register_duplicate_email_fails() -> None:
    """Duplicate email registrations should be rejected."""
    client = create_test_client()

    payload = {"email": "dup@example.com", "password": "secure-password"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409


def test_login_success_returns_token() -> None:
    """Login should return a bearer access token for valid credentials."""
    client = create_test_client()

    payload = {"email": "login@example.com", "password": "secure-password"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    token_payload = response.json()
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]


def test_login_wrong_password_fails() -> None:
    """Login should reject incorrect passwords."""
    client = create_test_client()

    client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "secure-password"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "bad-password"},
    )

    assert response.status_code == 401


def test_me_requires_token() -> None:
    """The /auth/me endpoint should require a bearer token."""
    client = create_test_client()

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user() -> None:
    """The /auth/me endpoint should return the authenticated user."""
    client = create_test_client()

    payload = {"email": "me@example.com", "password": "secure-password"}
    client.post("/auth/register", json=payload)
    login_response = client.post("/auth/login", json=payload)
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    user_payload = response.json()
    assert user_payload["email"] == "me@example.com"
