"""Feed model for RSS/Atom sources."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse, urlunparse

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base


def normalize_url(raw_url: str) -> str:
    """Normalize feed URLs for consistent storage and uniqueness."""
    stripped = raw_url.strip()
    parsed = urlparse(stripped)
    if not parsed.scheme or not parsed.netloc:
        return stripped

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path or ""
    if path.endswith("/") and path != "/":
        path = path[:-1]

    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


class Feed(Base):
    """Represents an RSS/Atom feed and its metadata."""

    __tablename__ = "feeds"
    __table_args__ = (UniqueConstraint("url", name="uq_feeds_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="Stored in canonical form for consistent deduplication.",
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    site_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @validates("url")
    def _normalize_url(self, _key: str, value: str) -> str:
        """Store canonical URLs to keep uniqueness constraints reliable."""
        return normalize_url(value)
