"""Rule model for conditional article aggregation.

Rules define criteria for matching articles from user's feeds/collections.
When executed, rules scan articles and store matches in RuleMatch table.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Rule(Base):
    """Defines a user's rule for keyword-based article matching.

    Rules allow users to create automated filters that identify articles
    matching specific criteria. Each rule belongs to a user and can optionally
    be scoped to a specific collection.

    Keyword storage rationale:
    - Keywords are stored as comma-separated text strings for simplicity.
    - This approach works across PostgreSQL and SQLite (for testing).
    - For more complex matching needs, consider JSON or array types later.
    - Example: "machine learning,neural network,AI" stores three keywords.

    Scheduling rationale:
    - frequency_minutes: How often the rule should be executed (in minutes).
    - last_run_at: Tracks when the rule was last executed to determine
      next scheduled run and to filter articles by time window.
    - is_active: Allows users to disable rules without deleting them.

    Indexing rationale:
    - (user_id): Enables efficient lookup of rules by owner.
    - (is_active): Supports filtering for only active rules during scheduling.
    - (last_run_at): Supports queries to find rules due for execution.
    """

    __tablename__ = "rules"
    __table_args__ = (
        # Index for listing rules by user
        Index("ix_rules_user_id", "user_id"),
        # Index for filtering active/inactive rules
        Index("ix_rules_is_active", "is_active"),
        # Index for scheduling queries (find rules due for execution)
        Index("ix_rules_last_run_at", "last_run_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Rule identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Keyword matching criteria (comma-separated text for cross-DB compatibility)
    # Example: "python,fastapi,backend" for include, "javascript,frontend" for exclude
    include_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclude_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional collection scope - if null, rule applies to all user's collections
    collection_id: Mapped[int | None] = mapped_column(
        ForeignKey("collections.id"), nullable=True
    )

    # Scheduling configuration
    frequency_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Rule state - allows disabling without deletion
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
