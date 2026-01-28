"""Tests for article read/saved state toggle endpoints.

These endpoints allow authenticated users to mark articles as read/unread
and saved/unsaved. All operations are idempotent and per-user scoped.

Timestamp behavior:
- PUT read: Sets is_read=true, read_at=now (only on transition from unread)
- DELETE read: Sets is_read=false, read_at=NULL
- PUT saved: Sets is_saved=true, saved_at=now (only on transition from unsaved)
- DELETE saved: Sets is_saved=false, saved_at=NULL
"""

from __future__ import annotations

from collections.abc import Iterator

from app.core.settings import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models.article import Article
from app.models.feed import Feed
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def create_test_client_with_session() -> tuple[TestClient, sessionmaker]:
    """Create a TestClient with an isolated in-memory database.

    Returns both the client and session factory to allow direct DB manipulation.
    """
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


def create_test_client() -> TestClient:
    """Create a TestClient with an isolated in-memory database."""
    client, _ = create_test_client_with_session()
    return client


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


def create_test_article(session_factory: sessionmaker) -> int:
    """Create a feed and article, returning the article ID."""
    session = session_factory()
    try:
        feed = Feed(url="https://example.com/rss", title="Test Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        article = Article(
            feed_id=feed.id,
            title="Test Article",
            url="https://example.com/article-1",
            guid="test-article-1",
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        return article.id
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Mark Read Tests
# -----------------------------------------------------------------------------


def test_mark_read_creates_state_row() -> None:
    """PUT /articles/{id}/read creates state row and sets is_read=true."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "reader@example.com")
    article_id = create_test_article(session_factory)

    response = client.put(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["article_id"] == article_id
    assert payload["is_read"] is True
    assert payload["read_at"] is not None
    assert payload["is_saved"] is False
    assert payload["saved_at"] is None


def test_mark_unread_sets_is_read_false() -> None:
    """DELETE /articles/{id}/read sets is_read=false and clears read_at."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "unread@example.com")
    article_id = create_test_article(session_factory)

    # First mark as read
    client.put(f"/api/v1/articles/{article_id}/read", headers=auth_headers(token))

    # Then mark as unread
    response = client.delete(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["article_id"] == article_id
    assert payload["is_read"] is False
    assert payload["read_at"] is None


# -----------------------------------------------------------------------------
# Mark Saved Tests
# -----------------------------------------------------------------------------


def test_mark_saved_creates_state_row() -> None:
    """PUT /articles/{id}/saved creates state row and sets is_saved=true."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "saver@example.com")
    article_id = create_test_article(session_factory)

    response = client.put(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["article_id"] == article_id
    assert payload["is_saved"] is True
    assert payload["saved_at"] is not None
    assert payload["is_read"] is False
    assert payload["read_at"] is None


def test_unsave_sets_is_saved_false() -> None:
    """DELETE /articles/{id}/saved sets is_saved=false and clears saved_at."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "unsave@example.com")
    article_id = create_test_article(session_factory)

    # First save
    client.put(f"/api/v1/articles/{article_id}/saved", headers=auth_headers(token))

    # Then unsave
    response = client.delete(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["article_id"] == article_id
    assert payload["is_saved"] is False
    assert payload["saved_at"] is None


# -----------------------------------------------------------------------------
# Idempotency Tests
# -----------------------------------------------------------------------------


def test_mark_read_idempotent() -> None:
    """Repeated PUT read does not error and preserves original read_at."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "idempotent-read@example.com")
    article_id = create_test_article(session_factory)

    # First mark as read
    response1 = client.put(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token),
    )
    assert response1.status_code == 200
    read_at_1 = response1.json()["read_at"]

    # Second mark as read (idempotent)
    response2 = client.put(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token),
    )
    assert response2.status_code == 200
    payload = response2.json()
    assert payload["is_read"] is True
    # Original read_at should be preserved
    assert payload["read_at"] == read_at_1


def test_mark_unread_idempotent() -> None:
    """Repeated DELETE read does not error when already unread."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "idempotent-unread@example.com")
    article_id = create_test_article(session_factory)

    # Mark as read then unread
    client.put(f"/api/v1/articles/{article_id}/read", headers=auth_headers(token))
    client.delete(f"/api/v1/articles/{article_id}/read", headers=auth_headers(token))

    # Second unread (idempotent)
    response = client.delete(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_read"] is False
    assert payload["read_at"] is None


def test_mark_saved_idempotent() -> None:
    """Repeated PUT saved does not error and preserves original saved_at."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "idempotent-save@example.com")
    article_id = create_test_article(session_factory)

    # First save
    response1 = client.put(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token),
    )
    assert response1.status_code == 200
    saved_at_1 = response1.json()["saved_at"]

    # Second save (idempotent)
    response2 = client.put(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token),
    )
    assert response2.status_code == 200
    payload = response2.json()
    assert payload["is_saved"] is True
    # Original saved_at should be preserved
    assert payload["saved_at"] == saved_at_1


def test_unsave_idempotent() -> None:
    """Repeated DELETE saved does not error when already unsaved."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "idempotent-unsave@example.com")
    article_id = create_test_article(session_factory)

    # Save then unsave
    client.put(f"/api/v1/articles/{article_id}/saved", headers=auth_headers(token))
    client.delete(f"/api/v1/articles/{article_id}/saved", headers=auth_headers(token))

    # Second unsave (idempotent)
    response = client.delete(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_saved"] is False
    assert payload["saved_at"] is None


def test_unread_without_prior_state_is_idempotent() -> None:
    """DELETE read on article without existing state creates unread state."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "no-state-unread@example.com")
    article_id = create_test_article(session_factory)

    # DELETE read without prior state
    response = client.delete(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["article_id"] == article_id
    assert payload["is_read"] is False
    assert payload["read_at"] is None


def test_unsave_without_prior_state_is_idempotent() -> None:
    """DELETE saved on article without existing state creates unsaved state."""
    client, session_factory = create_test_client_with_session()
    token = register_and_login(client, "no-state-unsave@example.com")
    article_id = create_test_article(session_factory)

    # DELETE saved without prior state
    response = client.delete(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["article_id"] == article_id
    assert payload["is_saved"] is False
    assert payload["saved_at"] is None


# -----------------------------------------------------------------------------
# Per-User State Isolation Tests
# -----------------------------------------------------------------------------


def test_user_state_isolation_read() -> None:
    """User A marking read does not affect user B's state."""
    client, session_factory = create_test_client_with_session()
    token_a = register_and_login(client, "user-a@example.com")
    token_b = register_and_login(client, "user-b@example.com")
    article_id = create_test_article(session_factory)

    # User A marks as read
    response_a = client.put(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token_a),
    )
    assert response_a.status_code == 200
    assert response_a.json()["is_read"] is True

    # User B checks state (should not exist or be unread)
    response_b = client.put(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token_b),
    )
    # B's first interaction creates their own state
    assert response_b.status_code == 200
    assert response_b.json()["is_read"] is True

    # User A marks unread
    client.delete(f"/api/v1/articles/{article_id}/read", headers=auth_headers(token_a))

    # Verify A is unread but B is still read
    response_a_check = client.delete(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token_a),
    )
    assert response_a_check.json()["is_read"] is False

    response_b_check = client.put(
        f"/api/v1/articles/{article_id}/read",
        headers=auth_headers(token_b),
    )
    assert response_b_check.json()["is_read"] is True


def test_user_state_isolation_saved() -> None:
    """User A saving does not affect user B's state."""
    client, session_factory = create_test_client_with_session()
    token_a = register_and_login(client, "save-a@example.com")
    token_b = register_and_login(client, "save-b@example.com")
    article_id = create_test_article(session_factory)

    # User A saves
    response_a = client.put(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token_a),
    )
    assert response_a.status_code == 200
    assert response_a.json()["is_saved"] is True

    # User B creates their state (unsaved by default)
    response_b = client.delete(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token_b),
    )
    assert response_b.status_code == 200
    assert response_b.json()["is_saved"] is False

    # Verify A is still saved
    response_a_check = client.put(
        f"/api/v1/articles/{article_id}/saved",
        headers=auth_headers(token_a),
    )
    assert response_a_check.json()["is_saved"] is True


# -----------------------------------------------------------------------------
# Error Cases
# -----------------------------------------------------------------------------


def test_mark_read_nonexistent_article_returns_404() -> None:
    """PUT read on non-existent article returns 404."""
    client = create_test_client()
    token = register_and_login(client, "404-read@example.com")

    response = client.put(
        "/api/v1/articles/99999/read",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_mark_unread_nonexistent_article_returns_404() -> None:
    """DELETE read on non-existent article returns 404."""
    client = create_test_client()
    token = register_and_login(client, "404-unread@example.com")

    response = client.delete(
        "/api/v1/articles/99999/read",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_mark_saved_nonexistent_article_returns_404() -> None:
    """PUT saved on non-existent article returns 404."""
    client = create_test_client()
    token = register_and_login(client, "404-save@example.com")

    response = client.put(
        "/api/v1/articles/99999/saved",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_unsave_nonexistent_article_returns_404() -> None:
    """DELETE saved on non-existent article returns 404."""
    client = create_test_client()
    token = register_and_login(client, "404-unsave@example.com")

    response = client.delete(
        "/api/v1/articles/99999/saved",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_endpoints_require_authentication() -> None:
    """All article state endpoints require authentication."""
    client, session_factory = create_test_client_with_session()
    article_id = create_test_article(session_factory)

    # No auth header
    assert client.put(f"/api/v1/articles/{article_id}/read").status_code == 401
    assert client.delete(f"/api/v1/articles/{article_id}/read").status_code == 401
    assert client.put(f"/api/v1/articles/{article_id}/saved").status_code == 401
    assert client.delete(f"/api/v1/articles/{article_id}/saved").status_code == 401
