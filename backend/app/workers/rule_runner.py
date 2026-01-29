"""Rule execution worker for conditional article aggregation.

This module provides the core job function for executing rules against articles.
It can be invoked directly or wrapped in a Celery task when Celery is configured.

Execution Flow
--------------
1. Load the Rule by id (raises RuleNotFoundError if not found)
2. Determine candidate articles:
   - If rule.collection_id is set: only articles from feeds in that collection
   - If rule.collection_id is None: all articles in the system
3. Apply keyword matcher to each candidate article
4. Insert RuleMatch rows for matched articles (idempotent via unique constraint)
5. Update rule.last_run_at to current timestamp

Idempotency Strategy
--------------------
- The RuleMatch table has a unique constraint on (rule_id, article_id)
- When inserting matches, we check for existing matches first
- If a match already exists, we skip insertion (no duplicate rows)
- This makes the function safe to retry or re-run without side effects

Candidate Selection
-------------------
- Collection-scoped rules: Query articles whose feed_id is in the feeds
  linked to the collection via CollectionFeed.
- Unscoped rules: Query articles from feeds in ALL collections owned by
  the rule's user (rule.user_id). This ensures per-user isolation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.collection import Collection
from app.models.collection_feed import CollectionFeed
from app.models.rule import Rule
from app.models.rule_match import RuleMatch
from app.rules.matcher import matches_rule

logger = logging.getLogger(__name__)


class RuleNotFoundError(Exception):
    """Raised when a rule with the given id does not exist."""

    pass


@dataclass
class RunRuleResult:
    """Result of running a rule.

    Attributes:
        rule_id: The id of the executed rule.
        candidates: Number of articles considered as candidates.
        matched: Number of articles that matched the rule criteria.
        created: Number of new RuleMatch rows created.
        skipped: Number of matches skipped (already existed).
    """

    rule_id: int
    candidates: int
    matched: int
    created: int
    skipped: int


def _get_candidate_articles(
    session: Session,
    rule: Rule,
) -> list[Article]:
    """Get candidate articles for a rule based on its scope.

    Candidate Selection Logic:
    - If rule.collection_id is set: Only articles from feeds linked to
      that collection via CollectionFeed.
    - If rule.collection_id is None: Articles from feeds in ALL collections
      owned by rule.user_id (ensures per-user isolation).

    Args:
        session: Database session.
        rule: The rule to get candidates for.

    Returns:
        List of Article objects that are candidates for matching.
    """
    if rule.collection_id is not None:
        # Collection-scoped: get feed_ids from CollectionFeed
        feed_ids_query = select(CollectionFeed.feed_id).where(
            CollectionFeed.collection_id == rule.collection_id
        )
    else:
        # Unscoped: get feed_ids from ALL collections owned by the rule's user
        # This ensures per-user isolation in multi-tenant environments
        user_collection_ids = select(Collection.id).where(
            Collection.user_id == rule.user_id
        )
        feed_ids_query = select(CollectionFeed.feed_id).where(
            CollectionFeed.collection_id.in_(user_collection_ids)
        )

    feed_ids = session.execute(feed_ids_query).scalars().all()

    if not feed_ids:
        return []

    # Get articles from those feeds
    articles_query = select(Article).where(Article.feed_id.in_(feed_ids))

    return list(session.execute(articles_query).scalars().all())


def _get_existing_match_article_ids(
    session: Session,
    rule_id: int,
    article_ids: list[int],
) -> set[int]:
    """Get article ids that already have RuleMatch rows for this rule.

    This is used to implement idempotency - we skip creating matches
    for articles that were already matched in previous runs.

    Args:
        session: Database session.
        rule_id: The rule id to check matches for.
        article_ids: List of article ids to check.

    Returns:
        Set of article ids that already have matches for this rule.
    """
    if not article_ids:
        return set()

    existing_query = select(RuleMatch.article_id).where(
        RuleMatch.rule_id == rule_id,
        RuleMatch.article_id.in_(article_ids),
    )
    return set(session.execute(existing_query).scalars().all())


def run_rule(rule_id: int, session: Session) -> RunRuleResult:
    """Execute a rule against candidate articles and store matches.

    This function is idempotent - running it multiple times will not
    create duplicate RuleMatch rows. Existing matches are skipped.

    Args:
        rule_id: The id of the rule to execute.
        session: Database session for queries and persistence.

    Returns:
        RunRuleResult with execution statistics.

    Raises:
        RuleNotFoundError: If no rule exists with the given id.

    Example:
        >>> result = run_rule(rule_id=1, session=db_session)
        >>> print(f"Matched {result.matched}, created {result.created}")
    """
    logger.info("Starting rule execution", extra={"rule_id": rule_id})

    # Step 1: Load the rule
    rule = session.get(Rule, rule_id)
    if rule is None:
        logger.warning("Rule not found", extra={"rule_id": rule_id})
        raise RuleNotFoundError(f"Rule with id {rule_id} not found")

    # Step 2: Get candidate articles
    candidates = _get_candidate_articles(session, rule)
    logger.info(
        "Candidate articles retrieved",
        extra={"rule_id": rule_id, "candidates": len(candidates)},
    )

    # Step 3: Apply keyword matcher to each candidate
    matched_articles: list[Article] = []
    for article in candidates:
        if matches_rule(rule, article):
            matched_articles.append(article)

    logger.info(
        "Articles matched",
        extra={"rule_id": rule_id, "matched": len(matched_articles)},
    )

    # Step 4: Insert RuleMatch rows (idempotent)
    created = 0
    skipped = 0

    if matched_articles:
        matched_article_ids = [a.id for a in matched_articles]
        existing_ids = _get_existing_match_article_ids(
            session, rule_id, matched_article_ids
        )

        now = datetime.now(UTC)
        for article in matched_articles:
            if article.id in existing_ids:
                skipped += 1
                continue

            match = RuleMatch(
                rule_id=rule_id,
                article_id=article.id,
                matched_at=now,
            )
            session.add(match)
            created += 1

    # Step 5: Update last_run_at
    rule.last_run_at = datetime.now(UTC)

    # Commit all changes
    session.commit()

    logger.info(
        "Rule execution completed",
        extra={
            "rule_id": rule_id,
            "candidates": len(candidates),
            "matched": len(matched_articles),
            "created": created,
            "skipped": skipped,
        },
    )

    return RunRuleResult(
        rule_id=rule_id,
        candidates=len(candidates),
        matched=len(matched_articles),
        created=created,
        skipped=skipped,
    )
