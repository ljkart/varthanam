"""Tests for feed fetching worker logic."""

from __future__ import annotations

import httpx
import pytest
from app.db.base import Base
from app.models.article import Article, compute_dedup_key
from app.models.feed import Feed, normalize_url
from app.workers.feed_fetcher import FeedFetchError, fetch_feed_articles
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

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
      <pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate>
      <description>Summary one.</description>
      <author>writer@example.com</author>
    </item>
    <item>
      <title>Item Two</title>
      <link>https://example.com/item-two</link>
      <guid>item-two</guid>
      <pubDate>Tue, 02 Jan 2024 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

RSS_WITHOUT_GUID = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <link>https://example.com</link>
    <description>Sample feed</description>
    <item>
      <title>Item Without Guid</title>
      <link>HTTPS://Example.com/Item-Three/</link>
      <pubDate>Wed, 03 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def create_test_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _mock_response(url: str, content: bytes) -> httpx.Response:
    """Build an httpx response with a request for raise_for_status."""
    request = httpx.Request("GET", url)
    return httpx.Response(
        200,
        content=content,
        headers={"Content-Type": "application/rss+xml"},
        request=request,
    )


def test_fetch_feed_articles_inserts_new_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid feed entries should be inserted into the article table."""
    session = create_test_session()
    try:
        feed = Feed(url="https://example.com/rss", title="Example Feed")
        session.add(feed)
        session.commit()

        def mock_get(
            url: str, timeout: float, follow_redirects: bool
        ) -> httpx.Response:
            assert url == "https://example.com/rss"
            return _mock_response(url, RSS_BYTES)

        monkeypatch.setattr(httpx, "get", mock_get)

        result = fetch_feed_articles(session, feed.id)

        articles = (
            session.execute(select(Article).where(Article.feed_id == feed.id))
            .scalars()
            .all()
        )

        assert result.fetched_count == 2
        assert result.created_count == 2
        assert result.skipped_count == 0
        assert {article.title for article in articles} == {"Item One", "Item Two"}

        refreshed_feed = session.get(Feed, feed.id)
        assert refreshed_feed
        assert refreshed_feed.failure_count == 0
        assert refreshed_feed.last_fetched_at is not None
    finally:
        session.close()


def test_fetch_feed_articles_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated fetch runs should not create duplicate articles."""
    session = create_test_session()
    try:
        feed = Feed(url="https://example.com/rss", title="Example Feed")
        session.add(feed)
        session.commit()

        def mock_get(
            url: str, timeout: float, follow_redirects: bool
        ) -> httpx.Response:
            return _mock_response(url, RSS_BYTES)

        monkeypatch.setattr(httpx, "get", mock_get)

        first = fetch_feed_articles(session, feed.id)
        second = fetch_feed_articles(session, feed.id)

        articles = (
            session.execute(select(Article).where(Article.feed_id == feed.id))
            .scalars()
            .all()
        )

        assert first.created_count == 2
        assert second.created_count == 0
        assert second.skipped_count == 2
        assert len(articles) == 2
    finally:
        session.close()


def test_fetch_feed_articles_dedup_uses_url_when_guid_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback to URL should deduplicate when GUID is missing."""
    session = create_test_session()
    try:
        feed = Feed(url="https://example.com/rss", title="Example Feed")
        session.add(feed)
        session.commit()

        def mock_get(
            url: str, timeout: float, follow_redirects: bool
        ) -> httpx.Response:
            return _mock_response(url, RSS_WITHOUT_GUID)

        monkeypatch.setattr(httpx, "get", mock_get)

        fetch_feed_articles(session, feed.id)
        fetch_feed_articles(session, feed.id)

        articles = (
            session.execute(select(Article).where(Article.feed_id == feed.id))
            .scalars()
            .all()
        )

        assert len(articles) == 1
        normalized_url = normalize_url("HTTPS://Example.com/Item-Three/")
        expected_key = compute_dedup_key(None, normalized_url)
        assert articles[0].dedup_key == expected_key
    finally:
        session.close()


def test_fetch_feed_articles_network_failure_increments_failure_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Network errors should increment failure_count and insert nothing."""
    session = create_test_session()
    try:
        feed = Feed(url="https://example.com/rss", title="Example Feed")
        session.add(feed)
        session.commit()

        def mock_get(
            url: str, timeout: float, follow_redirects: bool
        ) -> httpx.Response:
            raise httpx.RequestError("boom", request=httpx.Request("GET", url))

        monkeypatch.setattr(httpx, "get", mock_get)

        with pytest.raises(FeedFetchError):
            fetch_feed_articles(session, feed.id)

        refreshed_feed = session.get(Feed, feed.id)
        assert refreshed_feed
        assert refreshed_feed.failure_count == 1

        articles = (
            session.execute(select(Article).where(Article.feed_id == feed.id))
            .scalars()
            .all()
        )
        assert len(articles) == 0
    finally:
        session.close()
