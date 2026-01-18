"""Service-layer logic for feed validation and persistence."""

from __future__ import annotations

from urllib.parse import urlparse

import feedparser
import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.feed import Feed, normalize_url
from app.models.user import User
from app.schemas.feeds import FeedCreate


def _validate_feed_url(raw_url: str) -> str:
    """Validate feed URLs and return a normalized version.

    Args:
        raw_url: User-provided feed URL.

    Returns:
        str: Normalized feed URL ready for storage.

    Raises:
        HTTPException: If the URL is missing a valid scheme/host.
    """
    stripped = raw_url.strip()
    parsed = urlparse(stripped)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid feed URL.",
        )
    # Normalize before uniqueness checks to avoid duplicates with trivial variants.
    return normalize_url(stripped)


def _is_feed_content_type(content_type: str) -> bool:
    """Return True when the Content-Type hints at an RSS/Atom payload."""
    lowered = content_type.lower()
    return any(token in lowered for token in ("xml", "rss", "atom"))


def fetch_feed_content(url: str) -> tuple[bytes, str | None]:
    """Fetch raw feed bytes from the network.

    Args:
        url: Normalized feed URL to request.

    Returns:
        tuple[bytes, str | None]: Response content and Content-Type header.

    Raises:
        HTTPException: When the network request fails or returns invalid content.
    """
    try:
        response = httpx.get(url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
    except httpx.RequestError:
        # Map network failures to 502 to indicate upstream issues.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch feed.",
        ) from None
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch feed.",
        ) from None

    content_type = response.headers.get("Content-Type")
    if content_type and not _is_feed_content_type(content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feed content type is not supported.",
        )
    return response.content, content_type


def parse_feed_content(content: bytes) -> feedparser.FeedParserDict:
    """Parse RSS/Atom content into a feedparser structure.

    Args:
        content: Raw bytes of the feed response body.

    Returns:
        feedparser.FeedParserDict: Parsed feed data.

    Raises:
        HTTPException: If the payload cannot be parsed.
    """
    parsed = feedparser.parse(content)
    if parsed.bozo or not parsed.feed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feed could not be parsed.",
        )
    return parsed


def _extract_feed_metadata(parsed: feedparser.FeedParserDict) -> dict[str, str | None]:
    """Extract feed metadata from parsed content."""
    title = (parsed.feed.get("title") or "").strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feed is missing a title.",
        )
    description = parsed.feed.get("subtitle") or parsed.feed.get("description")
    return {
        "title": title,
        "site_url": parsed.feed.get("link"),
        "description": description,
    }


def _ensure_unique_url(session: Session, url: str) -> None:
    """Ensure the feed URL is not already stored.

    Args:
        session: Database session for lookups.
        url: Normalized feed URL.

    Raises:
        HTTPException: If the feed already exists.
    """
    existing = session.execute(select(Feed).where(Feed.url == url)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feed already exists.",
        )


def create_feed(session: Session, _user: User, feed_in: FeedCreate) -> Feed:
    """Validate, normalize, and persist a feed URL.

    Args:
        session: Database session for persistence.
        _user: Authenticated user requesting the feed creation.
        feed_in: Input payload containing the feed URL.

    Returns:
        Feed: Newly created feed record.

    Raises:
        HTTPException: When validation, fetch, parse, or persistence fails.
    """
    normalized_url = _validate_feed_url(feed_in.url)
    _ensure_unique_url(session, normalized_url)

    content, _content_type = fetch_feed_content(normalized_url)
    parsed = parse_feed_content(content)
    metadata = _extract_feed_metadata(parsed)

    feed = Feed(
        url=normalized_url,
        title=metadata["title"],
        site_url=metadata["site_url"],
        description=metadata["description"],
    )
    session.add(feed)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feed already exists.",
        ) from None
    session.refresh(feed)
    return feed
