"""RuleMatch model for tracking articles matched by rules.

Stores the relationship between rules and articles they have matched,
preventing duplicate matches on repeated rule executions.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RuleMatch(Base):
    """Records an article matched by a rule execution.

    Each RuleMatch represents a single match between a rule and an article.
    The unique constraint on (rule_id, article_id) ensures that the same
    article is not matched twice by the same rule across multiple executions.

    Purpose:
    - Prevents duplicate notifications/highlights for already-matched articles.
    - Enables efficient "what's new since last check" queries.
    - Provides audit trail of when matches occurred.

    Uniqueness constraint rationale:
    - (rule_id, article_id): A rule should only match each article once.
    - This constraint is essential for idempotent rule execution - running
      the same rule multiple times won't create duplicate match records.
    - Different rules can match the same article (no cross-rule uniqueness).

    Note: Unlike UserArticleState, RuleMatch does not need user_id because
    rules already belong to users. The rule_id FK provides the user context.
    """

    __tablename__ = "rule_matches"
    __table_args__ = (
        # Ensures a rule can only match each article once (idempotency)
        UniqueConstraint(
            "rule_id",
            "article_id",
            name="uq_rule_matches_rule_id_article_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"), nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)

    # When the match was recorded (useful for sorting matches by recency)
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
