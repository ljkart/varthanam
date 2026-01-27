"""Tests for listing feeds in a collection endpoint."""

from __future__ import annotations

from collections.abc import Iterator

from app.core.settings import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models.collection_feed import CollectionFeed
from app.models.feed import Feed
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def create_test_client() -> tuple[TestClient, sessionmaker]:
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
    return TestClient(app), session_factory


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


def test_list_collection_feeds_returns_assigned_feeds() -> None:
    """Feeds assigned to the collection should be returned."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "feeds@example.com")

    # Create collection
    col_response = client.post(
        "/api/v1/collections",
        json={"name": "My Feeds"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    # Create feeds and assign to collection
    session = session_factory()
    try:
        feed1 = Feed(url="https://feed1.com/rss", title="Feed One")
        feed2 = Feed(url="https://feed2.com/rss", title="Feed Two")
        session.add_all([feed1, feed2])
        session.commit()
        session.refresh(feed1)
        session.refresh(feed2)

        link1 = CollectionFeed(collection_id=collection_id, feed_id=feed1.id)
        link2 = CollectionFeed(collection_id=collection_id, feed_id=feed2.id)
        session.add_all([link1, link2])
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/feeds",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    titles = [feed["title"] for feed in payload]
    assert "Feed One" in titles
    assert "Feed Two" in titles


def test_list_collection_feeds_excludes_unassigned_feeds() -> None:
    """Feeds not assigned to the collection should not be returned."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "exclude@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Selective"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed_in = Feed(url="https://in.com/rss", title="Assigned Feed")
        feed_out = Feed(url="https://out.com/rss", title="Unassigned Feed")
        session.add_all([feed_in, feed_out])
        session.commit()
        session.refresh(feed_in)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed_in.id)
        session.add(link)
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/feeds",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Assigned Feed"


def test_list_collection_feeds_empty_collection() -> None:
    """Collection with no feeds should return empty list."""
    client, _ = create_test_client()
    token = register_and_login(client, "empty@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Empty"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    response = client.get(
        f"/api/v1/collections/{collection_id}/feeds",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == []


def test_list_collection_feeds_access_control() -> None:
    """Users should not access feeds from another user's collection."""
    client, _ = create_test_client()
    owner_token = register_and_login(client, "owner@example.com")
    other_token = register_and_login(client, "other@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Private"},
        headers=auth_headers(owner_token),
    )
    collection_id = col_response.json()["id"]

    response = client.get(
        f"/api/v1/collections/{collection_id}/feeds",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 404


def test_list_collection_feeds_nonexistent_collection() -> None:
    """Requesting feeds for a nonexistent collection should return 404."""
    client, _ = create_test_client()
    token = register_and_login(client, "nonexistent@example.com")

    response = client.get(
        "/api/v1/collections/99999/feeds",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_list_collection_feeds_response_schema() -> None:
    """Response should include expected feed fields."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "schema@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Schema Test"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(
            url="https://schema.com/rss",
            title="Schema Feed",
            site_url="https://schema.com",
            description="A test feed",
        )
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/feeds",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    feed_data = payload[0]
    assert "id" in feed_data
    assert feed_data["title"] == "Schema Feed"
    assert feed_data["url"] == "https://schema.com/rss"
    assert feed_data["site_url"] == "https://schema.com"
    assert feed_data["description"] == "A test feed"
    assert "created_at" in feed_data
    assert "updated_at" in feed_data
