"""Tests for collection articles endpoint with pagination and sorting."""

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
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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


def test_collection_articles_returns_articles_from_assigned_feeds() -> None:
    """Articles from feeds in the collection should be returned."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "articles@example.com")

    # Create collection
    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Tech News"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    # Create feed and assign to collection directly in DB
    session = session_factory()
    try:
        feed = Feed(url="https://example.com/rss", title="Example Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)
        session.commit()

        # Add articles to the feed
        article1 = Article(
            feed_id=feed.id,
            title="Article One",
            url="https://example.com/article-1",
            guid="article-1",
            published_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
        )
        article2 = Article(
            feed_id=feed.id,
            title="Article Two",
            url="https://example.com/article-2",
            guid="article-2",
            published_at=datetime(2024, 1, 2, 10, 0, 0, tzinfo=UTC),
        )
        session.add_all([article1, article2])
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    titles = [item["title"] for item in payload["items"]]
    assert "Article One" in titles
    assert "Article Two" in titles


def test_collection_articles_excludes_articles_from_unassigned_feeds() -> None:
    """Articles from feeds NOT in the collection should NOT be returned."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "exclude@example.com")

    # Create collection
    col_response = client.post(
        "/api/v1/collections",
        json={"name": "My Collection"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        # Create two feeds
        feed_assigned = Feed(url="https://assigned.com/rss", title="Assigned Feed")
        feed_unassigned = Feed(
            url="https://unassigned.com/rss", title="Unassigned Feed"
        )
        session.add_all([feed_assigned, feed_unassigned])
        session.commit()
        session.refresh(feed_assigned)
        session.refresh(feed_unassigned)

        # Only assign one feed to the collection
        link = CollectionFeed(collection_id=collection_id, feed_id=feed_assigned.id)
        session.add(link)
        session.commit()

        # Add articles to both feeds
        article_in = Article(
            feed_id=feed_assigned.id,
            title="Article In Collection",
            url="https://assigned.com/article-1",
            guid="assigned-1",
        )
        article_out = Article(
            feed_id=feed_unassigned.id,
            title="Article NOT In Collection",
            url="https://unassigned.com/article-1",
            guid="unassigned-1",
        )
        session.add_all([article_in, article_out])
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "Article In Collection"


def test_collection_articles_ordering_published_at_desc_nulls_last() -> None:
    """Articles should be ordered by published_at desc, nulls last, then created_at desc."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "ordering@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Ordered"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(url="https://order.com/rss", title="Order Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)
        session.commit()

        # Articles with different published_at times and nulls
        # Ordering expected: newest first, nulls last
        article_newest = Article(
            feed_id=feed.id,
            title="Newest",
            url="https://order.com/newest",
            guid="newest",
            published_at=datetime(2024, 3, 1, 10, 0, 0, tzinfo=UTC),
        )
        article_middle = Article(
            feed_id=feed.id,
            title="Middle",
            url="https://order.com/middle",
            guid="middle",
            published_at=datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC),
        )
        article_oldest = Article(
            feed_id=feed.id,
            title="Oldest",
            url="https://order.com/oldest",
            guid="oldest",
            published_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
        )
        article_null_pub = Article(
            feed_id=feed.id,
            title="No Published Date",
            url="https://order.com/null-pub",
            guid="null-pub",
            published_at=None,
        )
        session.add_all(
            [article_oldest, article_null_pub, article_newest, article_middle]
        )
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    titles = [item["title"] for item in payload["items"]]
    # Expected order: Newest, Middle, Oldest, No Published Date (nulls last)
    assert titles == ["Newest", "Middle", "Oldest", "No Published Date"]


def test_collection_articles_pagination_limit_offset() -> None:
    """Pagination with limit and offset should return correct slices."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "pagination@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Paginated"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(url="https://paginate.com/rss", title="Paginate Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)
        session.commit()

        # Create 5 articles with sequential published dates
        articles = []
        for i in range(5):
            articles.append(
                Article(
                    feed_id=feed.id,
                    title=f"Article {i + 1}",
                    url=f"https://paginate.com/article-{i + 1}",
                    guid=f"paginate-{i + 1}",
                    published_at=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=UTC),
                )
            )
        session.add_all(articles)
        session.commit()
    finally:
        session.close()

    # Get first page (limit=2, offset=0)
    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?limit=2&offset=0",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert payload["limit"] == 2
    assert payload["offset"] == 0
    assert len(payload["items"]) == 2
    # Newest first (published_at desc)
    titles = [item["title"] for item in payload["items"]]
    assert titles == ["Article 5", "Article 4"]

    # Get second page (limit=2, offset=2)
    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?limit=2&offset=2",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert len(payload["items"]) == 2
    titles = [item["title"] for item in payload["items"]]
    assert titles == ["Article 3", "Article 2"]

    # Get last page (limit=2, offset=4)
    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?limit=2&offset=4",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "Article 1"


def test_collection_articles_pagination_defaults() -> None:
    """Default pagination should use limit=20, offset=0."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "defaults@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Defaults"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 20
    assert payload["offset"] == 0


def test_collection_articles_limit_max_100() -> None:
    """Limit should be capped at 100."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "maxlimit@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Max Limit"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    # Request with limit > 100 should be capped or rejected
    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?limit=200",
        headers=auth_headers(token),
    )

    # Expecting validation error (422) for exceeding max limit
    assert response.status_code == 422


def test_collection_articles_total_count_matches() -> None:
    """Total count should match the actual number of articles in the collection."""
    client, session_factory = create_test_client()
    token = register_and_login(client, "totalcount@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Count Test"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    session = session_factory()
    try:
        feed = Feed(url="https://count.com/rss", title="Count Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)
        session.commit()

        # Create 15 articles
        articles = []
        for i in range(15):
            articles.append(
                Article(
                    feed_id=feed.id,
                    title=f"Count Article {i + 1}",
                    url=f"https://count.com/article-{i + 1}",
                    guid=f"count-{i + 1}",
                )
            )
        session.add_all(articles)
        session.commit()
    finally:
        session.close()

    # Get with small limit but check total
    response = client.get(
        f"/api/v1/collections/{collection_id}/articles?limit=5",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 15
    assert len(payload["items"]) == 5


def test_collection_articles_access_control_blocks_other_users() -> None:
    """Users should not access articles from another user's collection."""
    client, session_factory = create_test_client()
    owner_token = register_and_login(client, "owner@example.com")
    other_token = register_and_login(client, "other@example.com")

    # Owner creates collection
    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Private Collection"},
        headers=auth_headers(owner_token),
    )
    collection_id = col_response.json()["id"]

    # Other user tries to access owner's collection articles
    response = client.get(
        f"/api/v1/collections/{collection_id}/articles",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 404


def test_collection_articles_returns_404_for_nonexistent_collection() -> None:
    """Requesting articles for a nonexistent collection should return 404."""
    client, _ = create_test_client()
    token = register_and_login(client, "nonexistent@example.com")

    response = client.get(
        "/api/v1/collections/99999/articles",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_collection_articles_empty_collection() -> None:
    """Empty collection should return empty items with total=0."""
    client, _ = create_test_client()
    token = register_and_login(client, "empty@example.com")

    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Empty Collection"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_collection_articles_response_schema() -> None:
    """Response should include expected article fields."""
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
        feed = Feed(url="https://schema.com/rss", title="Schema Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        link = CollectionFeed(collection_id=collection_id, feed_id=feed.id)
        session.add(link)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="Schema Article",
            url="https://schema.com/article-1",
            guid="schema-1",
            summary="This is a summary.",
            author="Author Name",
            published_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
        )
        session.add(article)
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/collections/{collection_id}/articles",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    item = payload["items"][0]
    # Check expected fields are present
    assert "id" in item
    assert "feed_id" in item
    assert item["title"] == "Schema Article"
    assert item["url"] == "https://schema.com/article-1"
    assert item["summary"] == "This is a summary."
    assert item["author"] == "Author Name"
    assert "published_at" in item
    assert "created_at" in item
