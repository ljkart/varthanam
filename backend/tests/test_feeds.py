"""Tests for feed validation and creation endpoint."""

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


def test_create_feed_validates_and_persists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid RSS feeds should be accepted and stored."""
    client = create_test_client()
    token = register_and_login(client, "feeds@example.com")

    def mock_fetch(url: str) -> tuple[bytes, str | None]:
        assert url == "https://example.com/rss"
        return RSS_BYTES, "application/rss+xml"

    monkeypatch.setattr(feed_service, "fetch_feed_content", mock_fetch)

    response = client.post(
        "/api/v1/feeds",
        json={"url": "https://example.com/rss/"},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Example Feed"
    assert payload["site_url"] == "https://example.com"
    assert payload["description"] == "Sample feed"
    assert payload["url"] == "https://example.com/rss"
    assert payload["id"]


def test_create_feed_rejects_invalid_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid URLs should return a 400 error."""
    client = create_test_client()
    token = register_and_login(client, "invalid-url@example.com")

    def should_not_fetch(_: str) -> tuple[bytes, str | None]:
        raise AssertionError("fetch should not run for invalid URLs")

    monkeypatch.setattr(feed_service, "fetch_feed_content", should_not_fetch)

    response = client.post(
        "/api/v1/feeds",
        json={"url": "not-a-url"},
        headers=auth_headers(token),
    )

    assert response.status_code == 400


def test_create_feed_rejects_unparsable_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unparsable feed content should return a 400 error."""
    client = create_test_client()
    token = register_and_login(client, "bad-feed@example.com")

    def mock_fetch(_: str) -> tuple[bytes, str | None]:
        return b"not a feed", "application/rss+xml"

    monkeypatch.setattr(feed_service, "fetch_feed_content", mock_fetch)

    response = client.post(
        "/api/v1/feeds",
        json={"url": "https://example.com/bad"},
        headers=auth_headers(token),
    )

    assert response.status_code == 400


def test_create_feed_rejects_duplicate_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Duplicate feed URLs should return a 409 error."""
    client = create_test_client()
    token = register_and_login(client, "duplicate-feed@example.com")

    def mock_fetch(_: str) -> tuple[bytes, str | None]:
        return RSS_BYTES, "application/rss+xml"

    monkeypatch.setattr(feed_service, "fetch_feed_content", mock_fetch)

    response = client.post(
        "/api/v1/feeds",
        json={"url": "https://example.com/rss"},
        headers=auth_headers(token),
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/feeds",
        json={"url": "https://example.com/rss"},
        headers=auth_headers(token),
    )

    assert response.status_code == 409
