"""UserArticleState model for per-user article read/saved state."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserArticleState(Base):
    """Tracks per-user read/saved state for articles.

    Each user has their own independent state for each article, enabling
    personalized reading experience without affecting other users.

    Indexing rationale:
    - (user_id, article_id) unique constraint: Ensures one state per user-article
      pair and provides fast lookups when checking/updating state.
    - (user_id, is_read): Enables efficient "unread articles" queries by filtering
      on user and read status without full table scans.
    - (user_id, is_saved): Enables efficient "saved articles" queries by filtering
      on user and saved status without full table scans.

    These indexes support the primary access patterns:
    1. Get/update state for a specific user-article pair
    2. List unread articles for a user
    3. List saved articles for a user
    """

    __tablename__ = "user_article_states"
    __table_args__ = (
        # Ensures one state record per user-article pair
        UniqueConstraint(
            "user_id",
            "article_id",
            name="uq_user_article_states_user_id_article_id",
        ),
        # Composite index for filtering unread articles per user.
        # Placing user_id first allows efficient range scans for a single user.
        Index("ix_user_article_states_user_id_is_read", "user_id", "is_read"),
        # Composite index for filtering saved articles per user.
        Index("ix_user_article_states_user_id_is_saved", "user_id", "is_saved"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)

    # Read state: tracks whether the user has read this article
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )
    # Saved state: tracks whether the user has bookmarked this article
    is_saved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0")
    )

    # Timestamps for when state changed (nullable - only set when action occurs)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    saved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Standard audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
