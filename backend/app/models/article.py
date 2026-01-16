"""Article model for items fetched from feeds."""

from __future__ import annotations

import hashlib
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def compute_dedup_key(guid: str | None, url: str | None) -> str:
    """Compute a stable deduplication key from guid or url."""
    source = guid or url
    if not source:
        raise ValueError("Article requires guid or url to compute dedup_key.")
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


class Article(Base):
    """Represents a single feed item stored for reading."""

    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint(
            "feed_id",
            "dedup_key",
            name="uq_articles_feed_id_dedup_key",
        ),  # Per-feed uniqueness allows identical GUIDs across separate feeds.
        Index("ix_articles_dedup_key", "dedup_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    guid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dedup_key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


@event.listens_for(Article, "before_insert")
def _article_before_insert(_mapper, _connection, target: Article) -> None:
    """Ensure dedup_key is set before inserting articles."""
    target.dedup_key = compute_dedup_key(target.guid, target.url)


@event.listens_for(Article, "before_update")
def _article_before_update(_mapper, _connection, target: Article) -> None:
    """Keep dedup_key aligned with guid/url updates."""
    target.dedup_key = compute_dedup_key(target.guid, target.url)
