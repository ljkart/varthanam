"""Tests for Rule and RuleMatch models.

These models support the conditional aggregation (rules engine) feature,
allowing users to define keyword-based rules that match articles from
their collections.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.db.base import Base
from app.models.article import Article
from app.models.collection import Collection
from app.models.feed import Feed
from app.models.rule import Rule
from app.models.rule_match import RuleMatch
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


def create_test_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


# -----------------------------------------------------------------------------
# Rule Model Tests
# -----------------------------------------------------------------------------


def test_create_rule_minimal() -> None:
    """Rule can be created with required fields only."""
    session = create_test_session()
    try:
        user = User(email="rules@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule = Rule(
            user_id=user.id,
            name="Tech News",
            frequency_minutes=60,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)

        assert rule.id is not None
        assert rule.user_id == user.id
        assert rule.name == "Tech News"
        assert rule.frequency_minutes == 60
        assert rule.is_active is True  # Default
        assert rule.include_keywords is None
        assert rule.exclude_keywords is None
        assert rule.collection_id is None
        assert rule.last_run_at is None
        assert rule.created_at is not None
        assert rule.updated_at is not None
    finally:
        session.close()


def test_create_rule_with_all_fields() -> None:
    """Rule can be created with all fields populated."""
    session = create_test_session()
    try:
        user = User(email="fullrule@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        collection = Collection(user_id=user.id, name="Tech")
        session.add(collection)
        session.commit()
        session.refresh(collection)

        now = datetime.now(UTC)
        rule = Rule(
            user_id=user.id,
            name="AI Research",
            include_keywords="machine learning,neural network,deep learning",
            exclude_keywords="crypto,bitcoin",
            collection_id=collection.id,
            frequency_minutes=30,
            last_run_at=now,
            is_active=False,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)

        assert rule.id is not None
        assert rule.name == "AI Research"
        assert rule.include_keywords == "machine learning,neural network,deep learning"
        assert rule.exclude_keywords == "crypto,bitcoin"
        assert rule.collection_id == collection.id
        assert rule.frequency_minutes == 30
        assert rule.last_run_at is not None
        assert rule.is_active is False
    finally:
        session.close()


def test_rule_belongs_to_user() -> None:
    """Rule must belong to a user (FK constraint)."""
    session = create_test_session()
    try:
        user = User(email="owner@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule = Rule(
            user_id=user.id,
            name="My Rule",
            frequency_minutes=60,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)

        assert rule.user_id == user.id
    finally:
        session.close()


def test_rule_collection_id_nullable() -> None:
    """Rule collection_id can be null (applies to all collections)."""
    session = create_test_session()
    try:
        user = User(email="global@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule = Rule(
            user_id=user.id,
            name="Global Rule",
            frequency_minutes=60,
            collection_id=None,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)

        assert rule.collection_id is None
    finally:
        session.close()


def test_rule_is_active_defaults_true() -> None:
    """Rule is_active should default to True."""
    session = create_test_session()
    try:
        user = User(email="active@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule = Rule(
            user_id=user.id,
            name="Active by Default",
            frequency_minutes=60,
        )
        session.add(rule)
        session.commit()
        session.refresh(rule)

        assert rule.is_active is True
    finally:
        session.close()


def test_multiple_rules_per_user() -> None:
    """User can have multiple rules."""
    session = create_test_session()
    try:
        user = User(email="multi@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule1 = Rule(user_id=user.id, name="Rule 1", frequency_minutes=60)
        rule2 = Rule(user_id=user.id, name="Rule 2", frequency_minutes=30)
        session.add_all([rule1, rule2])
        session.commit()

        session.refresh(rule1)
        session.refresh(rule2)

        assert rule1.id != rule2.id
        assert rule1.user_id == rule2.user_id == user.id
    finally:
        session.close()


# -----------------------------------------------------------------------------
# RuleMatch Model Tests
# -----------------------------------------------------------------------------


def test_create_rule_match() -> None:
    """RuleMatch can be created linking a rule to an article."""
    session = create_test_session()
    try:
        # Setup user, rule, feed, article
        user = User(email="match@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule = Rule(user_id=user.id, name="Match Rule", frequency_minutes=60)
        session.add(rule)
        session.commit()
        session.refresh(rule)

        feed = Feed(url="https://match.com/rss", title="Match Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        article = Article(
            feed_id=feed.id,
            title="Matched Article",
            url="https://match.com/article-1",
            guid="match-1",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Create match
        now = datetime.now(UTC)
        match = RuleMatch(
            rule_id=rule.id,
            article_id=article.id,
            matched_at=now,
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        assert match.id is not None
        assert match.rule_id == rule.id
        assert match.article_id == article.id
        assert match.matched_at is not None
    finally:
        session.close()


def test_rule_match_uniqueness_constraint() -> None:
    """Duplicate (rule_id, article_id) pairs should be rejected."""
    session = create_test_session()
    try:
        user = User(email="unique@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule = Rule(user_id=user.id, name="Unique Rule", frequency_minutes=60)
        session.add(rule)
        session.commit()
        session.refresh(rule)

        feed = Feed(url="https://unique.com/rss", title="Unique Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        article = Article(
            feed_id=feed.id,
            title="Unique Article",
            url="https://unique.com/article-1",
            guid="unique-1",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # First match should succeed
        match1 = RuleMatch(
            rule_id=rule.id,
            article_id=article.id,
            matched_at=datetime.now(UTC),
        )
        session.add(match1)
        session.commit()

        # Second match with same rule/article should fail
        match2 = RuleMatch(
            rule_id=rule.id,
            article_id=article.id,
            matched_at=datetime.now(UTC),
        )
        session.add(match2)

        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.close()


def test_rule_match_different_rules_same_article() -> None:
    """Different rules can match the same article."""
    session = create_test_session()
    try:
        user = User(email="diffrules@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule1 = Rule(user_id=user.id, name="Rule A", frequency_minutes=60)
        rule2 = Rule(user_id=user.id, name="Rule B", frequency_minutes=60)
        session.add_all([rule1, rule2])
        session.commit()
        session.refresh(rule1)
        session.refresh(rule2)

        feed = Feed(url="https://diffrules.com/rss", title="Different Rules Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        article = Article(
            feed_id=feed.id,
            title="Shared Article",
            url="https://diffrules.com/article-1",
            guid="diffrules-1",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Both rules can match the same article
        match1 = RuleMatch(
            rule_id=rule1.id,
            article_id=article.id,
            matched_at=datetime.now(UTC),
        )
        match2 = RuleMatch(
            rule_id=rule2.id,
            article_id=article.id,
            matched_at=datetime.now(UTC),
        )
        session.add_all([match1, match2])
        session.commit()

        session.refresh(match1)
        session.refresh(match2)

        assert match1.id != match2.id
        assert match1.article_id == match2.article_id == article.id
    finally:
        session.close()


def test_rule_match_same_rule_different_articles() -> None:
    """Same rule can match multiple different articles."""
    session = create_test_session()
    try:
        user = User(email="multi-match@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        rule = Rule(user_id=user.id, name="Multi Match", frequency_minutes=60)
        session.add(rule)
        session.commit()
        session.refresh(rule)

        feed = Feed(url="https://multi.com/rss", title="Multi Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        article1 = Article(
            feed_id=feed.id,
            title="Article 1",
            url="https://multi.com/article-1",
            guid="multi-1",
        )
        article2 = Article(
            feed_id=feed.id,
            title="Article 2",
            url="https://multi.com/article-2",
            guid="multi-2",
        )
        session.add_all([article1, article2])
        session.commit()
        session.refresh(article1)
        session.refresh(article2)

        # Same rule can match different articles
        match1 = RuleMatch(
            rule_id=rule.id,
            article_id=article1.id,
            matched_at=datetime.now(UTC),
        )
        match2 = RuleMatch(
            rule_id=rule.id,
            article_id=article2.id,
            matched_at=datetime.now(UTC),
        )
        session.add_all([match1, match2])
        session.commit()

        session.refresh(match1)
        session.refresh(match2)

        assert match1.rule_id == match2.rule_id == rule.id
        assert match1.article_id != match2.article_id
    finally:
        session.close()
