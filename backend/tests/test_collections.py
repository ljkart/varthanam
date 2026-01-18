"""Tests for collection CRUD endpoints with user scoping."""

from __future__ import annotations

from collections.abc import Iterator

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
    return TestClient(app)


def register_and_login(
    client: TestClient,
    email: str,
    password: str = "secure-password",
) -> str:
    """Register a user and return a bearer token."""
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    """Build authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {token}"}


def test_create_collection() -> None:
    """Authenticated users can create collections."""
    client = create_test_client()
    token = register_and_login(client, "creator@example.com")

    response = client.post(
        "/api/v1/collections",
        json={"name": "Research", "description": "Reading list"},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Research"
    assert payload["description"] == "Reading list"
    assert payload["id"]


def test_create_collection_requires_name() -> None:
    """Collection name should be required and non-empty."""
    client = create_test_client()
    token = register_and_login(client, "required@example.com")

    response = client.post(
        "/api/v1/collections",
        json={"name": ""},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_create_collection_rejects_duplicate_name_per_user() -> None:
    """Duplicate collection names for a user should be rejected."""
    client = create_test_client()
    token = register_and_login(client, "dup@example.com")

    payload = {"name": "Research"}
    response = client.post(
        "/api/v1/collections",
        json=payload,
        headers=auth_headers(token),
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/collections",
        json=payload,
        headers=auth_headers(token),
    )

    assert response.status_code == 409


def test_list_user_collections() -> None:
    """Users should only see their own collections."""
    client = create_test_client()
    token = register_and_login(client, "list@example.com")

    client.post(
        "/api/v1/collections",
        json={"name": "Alpha"},
        headers=auth_headers(token),
    )
    client.post(
        "/api/v1/collections",
        json={"name": "Beta"},
        headers=auth_headers(token),
    )

    response = client.get("/api/v1/collections", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert [collection["name"] for collection in payload] == ["Alpha", "Beta"]


def test_retrieve_collection() -> None:
    """Users can retrieve a single collection by id."""
    client = create_test_client()
    token = register_and_login(client, "reader@example.com")

    create_response = client.post(
        "/api/v1/collections",
        json={"name": "Inbox"},
        headers=auth_headers(token),
    )
    collection_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/collections/{collection_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == collection_id
    assert payload["name"] == "Inbox"


def test_update_collection() -> None:
    """Users can update their own collections."""
    client = create_test_client()
    token = register_and_login(client, "updater@example.com")

    create_response = client.post(
        "/api/v1/collections",
        json={"name": "Old Name"},
        headers=auth_headers(token),
    )
    collection_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/collections/{collection_id}",
        json={"name": "New Name"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "New Name"


def test_update_collection_rejects_duplicate_name() -> None:
    """Updating a collection to a duplicate name should be rejected."""
    client = create_test_client()
    token = register_and_login(client, "duplicate-update@example.com")

    first = client.post(
        "/api/v1/collections",
        json={"name": "Primary"},
        headers=auth_headers(token),
    ).json()
    second = client.post(
        "/api/v1/collections",
        json={"name": "Secondary"},
        headers=auth_headers(token),
    ).json()

    response = client.patch(
        f"/api/v1/collections/{second['id']}",
        json={"name": first["name"]},
        headers=auth_headers(token),
    )

    assert response.status_code == 409


def test_delete_collection() -> None:
    """Users can delete their collections."""
    client = create_test_client()
    token = register_and_login(client, "deleter@example.com")

    create_response = client.post(
        "/api/v1/collections",
        json={"name": "To Delete"},
        headers=auth_headers(token),
    )
    collection_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/collections/{collection_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/v1/collections/{collection_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_access_control_blocks_other_users() -> None:
    """Users should not access or modify another user's collections."""
    client = create_test_client()
    owner_token = register_and_login(client, "owner@example.com")
    other_token = register_and_login(client, "other@example.com")

    create_response = client.post(
        "/api/v1/collections",
        json={"name": "Private"},
        headers=auth_headers(owner_token),
    )
    collection_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/collections/{collection_id}",
        headers=auth_headers(other_token),
    )
    assert response.status_code == 404

    response = client.patch(
        f"/api/v1/collections/{collection_id}",
        json={"name": "Hacked"},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 404

    response = client.delete(
        f"/api/v1/collections/{collection_id}",
        headers=auth_headers(other_token),
    )
    assert response.status_code == 404
