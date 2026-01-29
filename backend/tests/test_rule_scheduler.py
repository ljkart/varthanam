"""Unit tests for rule scheduling logic.

Tests cover:
- Due rule detection based on last_run_at and frequency_minutes
- Inactive rules are never due
- run_due_rules executes only due rules
- Failure in one rule does not stop other rules
- last_run_at updated only for successfully run rules
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.db.base import Base
from app.models.article import Article
from app.models.collection import Collection
from app.models.collection_feed import CollectionFeed
from app.models.feed import Feed
from app.models.rule import Rule
from app.models.user import User
from app.workers.rule_scheduler import get_due_rules, run_due_rules
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_test_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


# --- Helper functions ---


def create_user(session: Session, email: str = "test@example.com") -> User:
    """Create a test user."""
    user = User(email=email, password_hash="hashed")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_feed(session: Session, url: str = "https://example.com/feed.xml") -> Feed:
    """Create a test feed."""
    feed = Feed(url=url, title="Test Feed")
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


def create_collection(session: Session, user: User) -> Collection:
    """Create a test collection."""
    collection = Collection(user_id=user.id, name="Test Collection")
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


def create_article(session: Session, feed: Feed, title: str) -> Article:
    """Create an article."""
    article = Article(
        feed_id=feed.id,
        title=title,
        guid=f"guid-{title.lower().replace(' ', '-')}",
        url=f"https://example.com/{title.lower().replace(' ', '-')}",
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


def link_feed_to_collection(
    session: Session, collection: Collection, feed: Feed
) -> None:
    """Link a feed to a collection."""
    cf = CollectionFeed(collection_id=collection.id, feed_id=feed.id)
    session.add(cf)
    session.commit()


def create_rule(
    session: Session,
    user: User,
    name: str = "Test Rule",
    frequency_minutes: int = 60,
    is_active: bool = True,
    last_run_at: datetime | None = None,
    include_keywords: str | None = None,
) -> Rule:
    """Create a rule."""
    rule = Rule(
        user_id=user.id,
        name=name,
        frequency_minutes=frequency_minutes,
        is_active=is_active,
        last_run_at=last_run_at,
        include_keywords=include_keywords,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


# --- Due rule detection tests ---


class TestGetDueRules:
    """Tests for get_due_rules function."""

    def test_rule_with_null_last_run_at_is_due(self):
        """Rule with last_run_at=NULL should be due immediately."""
        session = create_test_session()
        try:
            user = create_user(session, "null@example.com")
            rule = create_rule(
                session,
                user,
                name="Never Run",
                frequency_minutes=60,
                last_run_at=None,
            )

            now = datetime.now(UTC)
            due_rules = get_due_rules(now, session)

            assert len(due_rules) == 1
            assert due_rules[0].id == rule.id
        finally:
            session.close()

    def test_rule_within_frequency_is_not_due(self):
        """Rule run recently (within frequency) should not be due."""
        session = create_test_session()
        try:
            user = create_user(session, "recent@example.com")
            now = datetime.now(UTC)
            # Last run 30 minutes ago, frequency is 60 minutes
            last_run = now - timedelta(minutes=30)
            _rule = create_rule(
                session,
                user,
                name="Recent Run",
                frequency_minutes=60,
                last_run_at=last_run,
            )

            due_rules = get_due_rules(now, session)

            assert len(due_rules) == 0
        finally:
            session.close()

    def test_rule_beyond_frequency_is_due(self):
        """Rule past its frequency interval should be due."""
        session = create_test_session()
        try:
            user = create_user(session, "overdue@example.com")
            now = datetime.now(UTC)
            # Last run 90 minutes ago, frequency is 60 minutes
            last_run = now - timedelta(minutes=90)
            rule = create_rule(
                session,
                user,
                name="Overdue",
                frequency_minutes=60,
                last_run_at=last_run,
            )

            due_rules = get_due_rules(now, session)

            assert len(due_rules) == 1
            assert due_rules[0].id == rule.id
        finally:
            session.close()

    def test_rule_exactly_at_frequency_is_due(self):
        """Rule exactly at its frequency interval should be due."""
        session = create_test_session()
        try:
            user = create_user(session, "exact@example.com")
            now = datetime.now(UTC)
            # Last run exactly 60 minutes ago, frequency is 60 minutes
            last_run = now - timedelta(minutes=60)
            rule = create_rule(
                session,
                user,
                name="Exact",
                frequency_minutes=60,
                last_run_at=last_run,
            )

            due_rules = get_due_rules(now, session)

            assert len(due_rules) == 1
            assert due_rules[0].id == rule.id
        finally:
            session.close()

    def test_inactive_rule_is_never_due(self):
        """Inactive rules should never be returned as due."""
        session = create_test_session()
        try:
            user = create_user(session, "inactive@example.com")
            # Rule with NULL last_run_at but inactive
            _rule = create_rule(
                session,
                user,
                name="Inactive",
                frequency_minutes=60,
                is_active=False,
                last_run_at=None,
            )

            now = datetime.now(UTC)
            due_rules = get_due_rules(now, session)

            assert len(due_rules) == 0
        finally:
            session.close()

    def test_multiple_due_rules_returned(self):
        """Multiple due rules should all be returned."""
        session = create_test_session()
        try:
            user = create_user(session, "multi@example.com")
            now = datetime.now(UTC)
            old_time = now - timedelta(hours=2)

            rule1 = create_rule(
                session, user, name="Rule 1", frequency_minutes=60, last_run_at=None
            )
            rule2 = create_rule(
                session,
                user,
                name="Rule 2",
                frequency_minutes=60,
                last_run_at=old_time,
            )
            # Not due - recent run
            create_rule(
                session,
                user,
                name="Rule 3",
                frequency_minutes=60,
                last_run_at=now - timedelta(minutes=10),
            )

            due_rules = get_due_rules(now, session)

            due_ids = {r.id for r in due_rules}
            assert len(due_rules) == 2
            assert rule1.id in due_ids
            assert rule2.id in due_ids
        finally:
            session.close()

    def test_zero_frequency_is_never_due(self):
        """Rule with frequency_minutes=0 should never be due (disabled scheduling)."""
        session = create_test_session()
        try:
            user = create_user(session, "zero@example.com")
            _rule = create_rule(
                session,
                user,
                name="Zero Freq",
                frequency_minutes=0,
                last_run_at=None,
            )

            now = datetime.now(UTC)
            due_rules = get_due_rules(now, session)

            assert len(due_rules) == 0
        finally:
            session.close()


# --- run_due_rules tests ---


class TestRunDueRules:
    """Tests for run_due_rules function."""

    def test_run_due_rules_executes_due_rules_only(self):
        """run_due_rules should only execute rules that are due."""
        session = create_test_session()
        try:
            user = create_user(session, "run@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)
            create_article(session, feed, "Python Article")

            now = datetime.now(UTC)

            # Due rule (never run)
            due_rule = create_rule(
                session,
                user,
                name="Due Rule",
                frequency_minutes=60,
                last_run_at=None,
                include_keywords="python",
            )
            # Not due (recent run)
            not_due_rule = create_rule(
                session,
                user,
                name="Not Due",
                frequency_minutes=60,
                last_run_at=now - timedelta(minutes=10),
                include_keywords="python",
            )

            result = run_due_rules(now, session)

            assert result.rules_due == 1
            assert result.rules_run == 1
            assert result.failures == 0

            # Check that due_rule was run (has last_run_at updated)
            session.refresh(due_rule)
            assert due_rule.last_run_at is not None

            # Check that not_due_rule was NOT run (last_run_at unchanged)
            session.refresh(not_due_rule)
            # Should still be close to original value (handle SQLite naive datetime)
            last_run = not_due_rule.last_run_at
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=UTC)
            assert (now - last_run) < timedelta(minutes=15)
        finally:
            session.close()

    def test_run_due_rules_continues_on_failure(self):
        """Failure in one rule should not stop other rules from running."""
        session = create_test_session()
        try:
            user = create_user(session, "failure@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)
            create_article(session, feed, "Test Article")

            # Create two due rules
            rule1 = create_rule(
                session,
                user,
                name="Rule 1",
                frequency_minutes=60,
                last_run_at=None,
            )
            _rule2 = create_rule(
                session,
                user,
                name="Rule 2",
                frequency_minutes=60,
                last_run_at=None,
            )

            now = datetime.now(UTC)

            # Mock run_rule to fail on first rule, succeed on second
            with patch("app.workers.rule_scheduler.run_rule") as mock_run:

                def side_effect(rule_id, sess):
                    if rule_id == rule1.id:
                        raise RuntimeError("Simulated failure")
                    from app.workers.rule_runner import RunRuleResult

                    return RunRuleResult(
                        rule_id=rule_id, candidates=1, matched=1, created=1, skipped=0
                    )

                mock_run.side_effect = side_effect

                result = run_due_rules(now, session)

            assert result.rules_due == 2
            assert result.rules_run == 1  # Only one succeeded
            assert result.failures == 1
        finally:
            session.close()

    def test_run_due_rules_returns_correct_counters(self):
        """run_due_rules should return accurate counters."""
        session = create_test_session()
        try:
            user = create_user(session, "counters@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)
            create_article(session, feed, "Python Tips")

            # Three due rules
            for i in range(3):
                create_rule(
                    session,
                    user,
                    name=f"Rule {i}",
                    frequency_minutes=60,
                    last_run_at=None,
                )

            now = datetime.now(UTC)
            result = run_due_rules(now, session)

            assert result.rules_due == 3
            assert result.rules_run == 3
            assert result.failures == 0
        finally:
            session.close()

    def test_run_due_rules_no_due_rules(self):
        """run_due_rules with no due rules should return zeros."""
        session = create_test_session()
        try:
            user = create_user(session, "nodeue@example.com")
            now = datetime.now(UTC)

            # Only recent rule (not due)
            create_rule(
                session,
                user,
                name="Recent",
                frequency_minutes=60,
                last_run_at=now - timedelta(minutes=10),
            )

            result = run_due_rules(now, session)

            assert result.rules_due == 0
            assert result.rules_run == 0
            assert result.failures == 0
        finally:
            session.close()

    def test_last_run_at_not_updated_on_failure(self):
        """last_run_at should NOT be updated if rule execution fails."""
        session = create_test_session()
        try:
            user = create_user(session, "noupdate@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)
            create_article(session, feed, "Article")

            rule = create_rule(
                session,
                user,
                name="Will Fail",
                frequency_minutes=60,
                last_run_at=None,
            )

            now = datetime.now(UTC)

            # Mock run_rule to always fail
            with patch("app.workers.rule_scheduler.run_rule") as mock_run:
                mock_run.side_effect = RuntimeError("Simulated failure")

                result = run_due_rules(now, session)

            assert result.failures == 1

            # last_run_at should still be None
            session.refresh(rule)
            assert rule.last_run_at is None
        finally:
            session.close()

    def test_last_run_at_updated_on_success(self):
        """last_run_at should be updated after successful rule execution."""
        session = create_test_session()
        try:
            user = create_user(session, "success@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)
            create_article(session, feed, "Article")

            rule = create_rule(
                session,
                user,
                name="Will Succeed",
                frequency_minutes=60,
                last_run_at=None,
            )

            now = datetime.now(UTC)
            run_due_rules(now, session)

            session.refresh(rule)
            assert rule.last_run_at is not None
        finally:
            session.close()
