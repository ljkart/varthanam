"""Tests for assigning and unassigning feeds to collections."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.core.settings import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.services import feeds as feed_service
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

RSS_BYTES = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <link>https://example.com</link>
    <description>Sample feed</description>
    <item>
      <title>Item One</title>
      <link>https://example.com/item-one</link>
      <guid>item-one</guid>
    </item>
  </channel>
</rss>
"""


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


def create_collection(client: TestClient, token: str, name: str = "Inbox") -> int:
    """Create a collection and return its id."""
    response = client.post(
        "/api/v1/collections",
        json={"name": name},
        headers=auth_headers(token),
    )
    return response.json()["id"]


def create_feed(
    client: TestClient,
    token: str,
    monkeypatch: pytest.MonkeyPatch,
    url: str = "https://example.com/rss",
) -> int:
    """Create a feed via the API and return its id."""

    def mock_fetch(requested_url: str) -> tuple[bytes, str | None]:
        assert requested_url == url
        return RSS_BYTES, "application/rss+xml"

    monkeypatch.setattr(feed_service, "fetch_feed_content", mock_fetch)

    response = client.post(
        "/api/v1/feeds",
        json={"url": url},
        headers=auth_headers(token),
    )
    return response.json()["id"]


def test_assign_feed_to_collection_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Users can assign a feed to their own collection."""
    client = create_test_client()
    token = register_and_login(client, "assign@example.com")

    collection_id = create_collection(client, token)
    feed_id = create_feed(client, token, monkeypatch)

    response = client.post(
        f"/api/v1/collections/{collection_id}/feeds",
        json={"feed_id": feed_id},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["collection_id"] == collection_id
    assert payload["feed_id"] == feed_id


def test_assign_feed_twice_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assigning the same feed twice returns a stable relationship."""
    client = create_test_client()
    token = register_and_login(client, "idempotent@example.com")

    collection_id = create_collection(client, token)
    feed_id = create_feed(client, token, monkeypatch)

    response = client.post(
        f"/api/v1/collections/{collection_id}/feeds",
        json={"feed_id": feed_id},
        headers=auth_headers(token),
    )
    assert response.status_code == 201

    response = client.post(
        f"/api/v1/collections/{collection_id}/feeds",
        json={"feed_id": feed_id},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["collection_id"] == collection_id
    assert payload["feed_id"] == feed_id


def test_unassign_feed_from_collection_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Users can remove a feed from their collection."""
    client = create_test_client()
    token = register_and_login(client, "unassign@example.com")

    collection_id = create_collection(client, token)
    feed_id = create_feed(client, token, monkeypatch)

    client.post(
        f"/api/v1/collections/{collection_id}/feeds",
        json={"feed_id": feed_id},
        headers=auth_headers(token),
    )

    response = client.delete(
        f"/api/v1/collections/{collection_id}/feeds/{feed_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204


def test_unassign_missing_link_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removing a missing link should still succeed."""
    client = create_test_client()
    token = register_and_login(client, "missing-link@example.com")

    collection_id = create_collection(client, token)
    feed_id = create_feed(client, token, monkeypatch)

    response = client.delete(
        f"/api/v1/collections/{collection_id}/feeds/{feed_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204


def test_other_users_cannot_manage_collection_feeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Users cannot assign or unassign feeds on collections they do not own."""
    client = create_test_client()
    owner_token = register_and_login(client, "owner-assign@example.com")
    other_token = register_and_login(client, "other-assign@example.com")

    collection_id = create_collection(client, owner_token)
    feed_id = create_feed(client, owner_token, monkeypatch)

    response = client.post(
        f"/api/v1/collections/{collection_id}/feeds",
        json={"feed_id": feed_id},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 404

    response = client.delete(
        f"/api/v1/collections/{collection_id}/feeds/{feed_id}",
        headers=auth_headers(other_token),
    )
    assert response.status_code == 404


def test_assign_feed_requires_existing_collection_and_feed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assigning requires both the collection and feed to exist."""
    client = create_test_client()
    token = register_and_login(client, "missing-resources@example.com")

    feed_id = create_feed(client, token, monkeypatch)

    response = client.post(
        "/api/v1/collections/999/feeds",
        json={"feed_id": feed_id},
        headers=auth_headers(token),
    )
    assert response.status_code == 404

    collection_id = create_collection(client, token)
    response = client.post(
        f"/api/v1/collections/{collection_id}/feeds",
        json={"feed_id": 999},
        headers=auth_headers(token),
    )
    assert response.status_code == 404


def test_unassign_requires_existing_feed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unassigning should return 404 when the feed is missing."""
    client = create_test_client()
    token = register_and_login(client, "missing-feed-delete@example.com")

    collection_id = create_collection(client, token)
    create_feed(client, token, monkeypatch)

    response = client.delete(
        f"/api/v1/collections/{collection_id}/feeds/999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
