"""Fetch feed entries and persist them as articles."""

from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article, compute_dedup_key
from app.models.feed import Feed

logger = logging.getLogger(__name__)


class FeedFetchError(RuntimeError):
    """Raised when a feed fetch or parse operation fails."""


@dataclass(frozen=True)
class FeedFetchResult:
    """Counts for a feed fetch execution."""

    feed_id: int
    fetched_count: int
    created_count: int
    skipped_count: int


def _parse_entry_datetime(value) -> datetime | None:
    """Convert feedparser timestamps into timezone-aware datetimes."""
    if not value:
        return None
    return datetime.fromtimestamp(calendar.timegm(value), tz=UTC)


def _parse_http_datetime(value: str | None) -> datetime | None:
    """Parse HTTP datetime headers into timezone-aware datetimes."""
    if not value:
        return None
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _extract_entry_content(entry: feedparser.FeedParserDict) -> str | None:
    """Pull content text from feedparser entries when available."""
    content_items = entry.get("content")
    if content_items:
        content_value = content_items[0].get("value")
        if content_value:
            return content_value
    return None


def _mark_fetch_failure(session: Session, feed: Feed) -> None:
    """Increment failure_count and persist feed failure state."""
    session.rollback()
    feed.failure_count += 1
    session.add(feed)
    session.commit()


def fetch_feed_articles(session: Session, feed_id: int) -> FeedFetchResult:
    """Fetch feed entries via HTTP and persist them as Articles.

    Args:
        session: Database session used for reads/writes.
        feed_id: Feed identifier to fetch.

    Returns:
        FeedFetchResult: Counts of fetched, created, and skipped entries.

    Raises:
        FeedFetchError: If the network request or parsing fails.
        ValueError: If the feed does not exist.
    """
    feed = session.get(Feed, feed_id)
    if not feed:
        raise ValueError(f"Feed {feed_id} not found.")

    try:
        response = httpx.get(feed.url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if parsed.bozo:
            raise FeedFetchError("Feed parsing failed.")
    except (httpx.RequestError, httpx.HTTPStatusError) as exc:
        _mark_fetch_failure(session, feed)
        logger.warning("Feed fetch failed feed_id=%s error=%s", feed_id, exc.__class__)
        raise FeedFetchError("Feed fetch failed.") from exc
    except FeedFetchError:
        _mark_fetch_failure(session, feed)
        logger.warning("Feed parse failed feed_id=%s", feed_id)
        raise

    entries = list(parsed.entries or [])
    fetched_count = len(entries)
    skipped_count = 0
    created_count = 0

    candidates: list[tuple[str, feedparser.FeedParserDict]] = []
    for entry in entries:
        guid = entry.get("id") or entry.get("guid")
        url = entry.get("link")
        try:
            dedup_key = compute_dedup_key(guid, url)
        except ValueError:
            skipped_count += 1
            continue
        candidates.append((dedup_key, entry))

    candidate_keys = {dedup_key for dedup_key, _entry in candidates}
    existing_keys: set[str] = set()
    if candidate_keys:
        existing_keys = set(
            session.execute(
                select(Article.dedup_key).where(
                    Article.feed_id == feed.id,
                    Article.dedup_key.in_(candidate_keys),
                )
            )
            .scalars()
            .all()
        )

    seen_keys = set(existing_keys)
    for dedup_key, entry in candidates:
        if dedup_key in seen_keys:
            skipped_count += 1
            continue

        title = (entry.get("title") or "").strip() or "Untitled"
        summary = entry.get("summary") or entry.get("description")
        published_at = _parse_entry_datetime(
            entry.get("published_parsed") or entry.get("updated_parsed")
        )

        article = Article(
            feed_id=feed.id,
            title=title,
            url=entry.get("link"),
            guid=entry.get("id") or entry.get("guid"),
            published_at=published_at,
            summary=summary,
            content=_extract_entry_content(entry),
            author=entry.get("author"),
        )
        session.add(article)
        seen_keys.add(dedup_key)
        created_count += 1

    feed.last_fetched_at = datetime.now(UTC)
    feed.failure_count = 0
    feed.etag = response.headers.get("ETag") or feed.etag
    feed.last_modified = _parse_http_datetime(
        response.headers.get("Last-Modified")
    ) or (feed.last_modified)

    session.add(feed)
    session.commit()

    logger.info(
        "Feed fetch complete feed_id=%s fetched=%s created=%s skipped=%s",
        feed_id,
        fetched_count,
        created_count,
        skipped_count,
    )

    return FeedFetchResult(
        feed_id=feed.id,
        fetched_count=fetched_count,
        created_count=created_count,
        skipped_count=skipped_count,
    )
