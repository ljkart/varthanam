"""Tests for article listing filters (unread_only, saved_only).

These filters allow users to filter collection articles by their personal
read/saved state. Filter behavior:

- unread_only=true: Returns articles where user has no state row (treated as unread)
  OR state.is_read=false.
- saved_only=true: Returns articles where state row exists AND is_saved=true.
- Both filters together: Intersection (unread AND saved).

All filters are per-user - one user's state does not affect another's results.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

from app.core.settings import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models.article import Article
from app.models.collection_feed import CollectionFeed
from app.models.feed import Feed
from app.models.user import User
from app.models.user_article_state import UserArticleState
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def create_test_client() -> tuple[TestClient, sessionmaker]:
    """Create a TestClient with an isolated in-memory database.

    Returns:
        Tuple of TestClient and session factory for direct DB access in tests.
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


def get_user_id(session_factory: sessionmaker, email: str) -> int:
    """Get user ID by email from the database."""
    session = session_factory()
    try:
        user = session.execute(select(User).where(User.email == email)).scalar_one()
        return user.id
    finally:
        session.close()


def setup_collection_with_articles(
    client: TestClient,
    session_factory: sessionmaker,
    token: str,
    email: str,
) -> tuple[int, list[int]]:
    """Create a collection with 4 articles for testing filters.

    Creates articles with different states for the user:
    - Article 1: No state row (unread by default)
    - Article 2: is_read=true (read)
    - Article 3: is_saved=true, is_read=false (saved, unread)
    - Article 4: is_read=true, is_saved=true (read and saved)

    Returns:
        Tuple of (collection_id, [article_1_id, article_2_id, article_3_id, article_4_id])
    """
    # Create collection
    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Filter Test Collection"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        # Create feed
        feed = Feed(url=f"https://filter-{email}.com/rss", title="Filter Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        # Assign feed to collection
        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)
        session.commit()

        # Create 4 articles with sequential published dates for predictable ordering
        articles = []
        for i in range(4):
            article = Article(
                feed_id=feed.id,
                title=f"Article {i + 1}",
                url=f"https://filter-{email}.com/article-{i + 1}",
                guid=f"filter-{email}-{i + 1}",
                published_at=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=UTC),
            )
            session.add(article)
        session.commit()

        # Refresh to get IDs
        for article in session.execute(
            select(Article).where(Article.feed_id == feed.id).order_by(Article.id)
        ).scalars():
            articles.append(article)

        article_ids = [a.id for a in articles]

        # Get user ID
        user_id = get_user_id(session_factory, email)

        # Set up states:
        # Article 1: No state (unread by default)
        # Article 2: is_read=true
        state2 = UserArticleState(
            user_id=user_id,
            article_id=article_ids[1],
            is_read=True,
            read_at=datetime.now(UTC),
        )
        # Article 3: is_saved=true, is_read=false
        state3 = UserArticleState(
            user_id=user_id,
            article_id=article_ids[2],
            is_read=False,
            is_saved=True,
            saved_at=datetime.now(UTC),
        )
        # Article 4: is_read=true, is_saved=true
        state4 = UserArticleState(
            user_id=user_id,
            article_id=article_ids[3],
            is_read=True,
            read_at=datetime.now(UTC),
            is_saved=True,
            saved_at=datetime.now(UTC),
        )
        session.add_all([state2, state3, state4])
        session.commit()

        return collection_id, article_ids
    finally:
        session.close()


# -----------------------------------------------------------------------------
# unread_only Filter Tests
# -----------------------------------------------------------------------------


def test_unread_only_returns_unread_articles() -> None:
    """unread_only=true returns articles with no state row or is_read=false."""
    client, session_factory = create_test_client()
    email = "unread-filter@example.com"
    token = register_and_login(client, email)
    collection_id, article_ids = setup_collection_with_articles(
        client, session_factory, token, email
    )

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=true",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    # Should return Article 1 (no state) and Article 3 (is_read=false)
    assert payload["total"] == 2
    titles = [item["title"] for item in payload["items"]]
    assert "Article 1" in titles
    assert "Article 3" in titles
    assert "Article 2" not in titles  # is_read=true
    assert "Article 4" not in titles  # is_read=true


def test_unread_only_false_returns_all_articles() -> None:
    """unread_only=false (default) returns all articles."""
    client, session_factory = create_test_client()
    email = "unread-false@example.com"
    token = register_and_login(client, email)
    collection_id, _ = setup_collection_with_articles(
        client, session_factory, token, email
    )

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=false",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4


def test_unread_only_treats_missing_state_as_unread() -> None:
    """Articles without a UserArticleState row are treated as unread."""
    client, session_factory = create_test_client()
    email = "missing-state@example.com"
    token = register_and_login(client, email)

    # Create collection with articles but no state rows
    col_response = client.post(
        "/api/v1/collections",
        json={"name": "No State Collection"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(url="https://nostate.com/rss", title="No State Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)

        article = Article(
            feed_id=feed.id,
            title="No State Article",
            url="https://nostate.com/article-1",
            guid="nostate-1",
        )
        session.add(article)
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=true",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "No State Article"


# -----------------------------------------------------------------------------
# saved_only Filter Tests
# -----------------------------------------------------------------------------


def test_saved_only_returns_saved_articles() -> None:
    """saved_only=true returns only articles with is_saved=true."""
    client, session_factory = create_test_client()
    email = "saved-filter@example.com"
    token = register_and_login(client, email)
    collection_id, article_ids = setup_collection_with_articles(
        client, session_factory, token, email
    )

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?saved_only=true",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    # Should return Article 3 and Article 4 (both have is_saved=true)
    assert payload["total"] == 2
    titles = [item["title"] for item in payload["items"]]
    assert "Article 3" in titles
    assert "Article 4" in titles
    assert "Article 1" not in titles  # No state (unsaved)
    assert "Article 2" not in titles  # is_saved=false


def test_saved_only_false_returns_all_articles() -> None:
    """saved_only=false (default) returns all articles."""
    client, session_factory = create_test_client()
    email = "saved-false@example.com"
    token = register_and_login(client, email)
    collection_id, _ = setup_collection_with_articles(
        client, session_factory, token, email
    )

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?saved_only=false",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4


def test_saved_only_excludes_articles_without_state() -> None:
    """Articles without a UserArticleState row are excluded when saved_only=true."""
    client, session_factory = create_test_client()
    email = "saved-nostate@example.com"
    token = register_and_login(client, email)

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Saved No State"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(url="https://savednostate.com/rss", title="Saved No State Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)

        article = Article(
            feed_id=feed.id,
            title="Unsaved Article",
            url="https://savednostate.com/article-1",
            guid="savednostate-1",
        )
        session.add(article)
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?saved_only=true",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["items"] == []


# -----------------------------------------------------------------------------
# Combined Filters Tests
# -----------------------------------------------------------------------------


def test_both_filters_returns_intersection() -> None:
    """unread_only=true AND saved_only=true returns unread AND saved articles."""
    client, session_factory = create_test_client()
    email = "both-filters@example.com"
    token = register_and_login(client, email)
    collection_id, article_ids = setup_collection_with_articles(
        client, session_factory, token, email
    )

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=true&saved_only=true",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    # Only Article 3 is both unread (is_read=false) and saved (is_saved=true)
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "Article 3"


def test_both_filters_empty_when_no_match() -> None:
    """Combined filters return empty when no articles match both criteria."""
    client, session_factory = create_test_client()
    email = "no-match@example.com"
    token = register_and_login(client, email)

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "No Match"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(url="https://nomatch.com/rss", title="No Match Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)

        article = Article(
            feed_id=feed.id,
            title="Read Article",
            url="https://nomatch.com/article-1",
            guid="nomatch-1",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Mark as read but not saved
        user_id = get_user_id(session_factory, email)
        state = UserArticleState(
            user_id=user_id,
            article_id=article.id,
            is_read=True,
            read_at=datetime.now(UTC),
            is_saved=False,
        )
        session.add(state)
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=true&saved_only=true",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0


# -----------------------------------------------------------------------------
# Per-User State Isolation Tests
# -----------------------------------------------------------------------------


def test_filters_are_per_user() -> None:
    """User A's state does not affect user B's filtered results."""
    client, session_factory = create_test_client()

    email_a = "user-a-filter@example.com"
    email_b = "user-b-filter@example.com"
    token_a = register_and_login(client, email_a)
    token_b = register_and_login(client, email_b)

    # User A creates collection
    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Shared Articles"},
        headers=auth_headers(token_a),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(url="https://peruser.com/rss", title="Per User Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)

        article = Article(
            feed_id=feed.id,
            title="Shared Article",
            url="https://peruser.com/article-1",
            guid="peruser-1",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # User A marks as read
        user_a_id = get_user_id(session_factory, email_a)
        state_a = UserArticleState(
            user_id=user_a_id,
            article_id=article.id,
            is_read=True,
            read_at=datetime.now(UTC),
        )
        session.add(state_a)
        session.commit()
    finally:
        session.close()

    # User A sees no unread articles
    response_a = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=true",
        headers=auth_headers(token_a),
    )
    assert response_a.status_code == 200
    assert response_a.json()["total"] == 0

    # User B creates their own collection with the same feed
    col_response_b = client.post(
        "/api/v1/collections",
        json={"name": "User B Collection"},
        headers=auth_headers(token_b),
    )
    collection_id_b = col_response_b.json()["id"]

    session = session_factory()
    try:
        feed = session.execute(
            select(Feed).where(Feed.url == "https://peruser.com/rss")
        ).scalar_one()
        link_b = CollectionFeed(collection_id=collection_id_b, feed_id=feed.id)
        session.add(link_b)
        session.commit()
    finally:
        session.close()

    # User B sees the article as unread (no state for B)
    response_b = client.get(
        f"/api/v1/collections/{collection_id_b}/articles?unread_only=true",
        headers=auth_headers(token_b),
    )
    assert response_b.status_code == 200
    assert response_b.json()["total"] == 1
    assert response_b.json()["items"][0]["title"] == "Shared Article"


# -----------------------------------------------------------------------------
# Ordering and Pagination with Filters Tests
# -----------------------------------------------------------------------------


def test_filters_maintain_ordering() -> None:
    """Filtered results maintain published_at DESC ordering."""
    client, session_factory = create_test_client()
    email = "order-filter@example.com"
    token = register_and_login(client, email)
    collection_id, article_ids = setup_collection_with_articles(
        client, session_factory, token, email
    )

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=true",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    titles = [item["title"] for item in payload["items"]]
    # Article 3 (Jan 3) should come before Article 1 (Jan 1) - newest first
    assert titles == ["Article 3", "Article 1"]


def test_filters_with_pagination() -> None:
    """Filters work correctly with pagination."""
    client, session_factory = create_test_client()
    email = "paginate-filter@example.com"
    token = register_and_login(client, email)

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Paginate Filter"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(url="https://pagfilter.com/rss", title="Paginate Filter Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)

        # Create 5 articles, all unread (no state)
        for i in range(5):
            article = Article(
                feed_id=feed.id,
                title=f"Unread Article {i + 1}",
                url=f"https://pagfilter.com/article-{i + 1}",
                guid=f"pagfilter-{i + 1}",
                published_at=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=UTC),
            )
            session.add(article)
        session.commit()
    finally:
        session.close()

    # Get first page with limit=2
    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=true&limit=2&offset=0",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert len(payload["items"]) == 2
    assert payload["limit"] == 2
    assert payload["offset"] == 0
    # Newest first
    titles = [item["title"] for item in payload["items"]]
    assert titles == ["Unread Article 5", "Unread Article 4"]

    # Get second page
    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?unread_only=true&limit=2&offset=2",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert len(payload["items"]) == 2
    titles = [item["title"] for item in payload["items"]]
    assert titles == ["Unread Article 3", "Unread Article 2"]


def test_default_filter_values_return_all() -> None:
    """Endpoint without filter params returns all articles (backward compatible)."""
    client, session_factory = create_test_client()
    email = "default-filters@example.com"
    token = register_and_login(client, email)
    collection_id, _ = setup_collection_with_articles(
        client, session_factory, token, email
    )

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    # All 4 articles returned when no filters specified
    assert payload["total"] == 4
