"""Association model between collections and feeds."""

from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CollectionFeed(Base):
    """Links feeds to collections in a many-to-many relationship."""

    __tablename__ = "collection_feeds"
    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "feed_id",
            name="uq_collection_feeds_collection_id_feed_id",
        ),
    )

    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id"), primary_key=True
    )
    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id"), primary_key=True)
