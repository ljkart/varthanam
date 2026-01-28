"""Tests for UserArticleState model."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.db.base import Base
from app.models.article import Article
from app.models.feed import Feed
from app.models.user import User
from app.models.user_article_state import UserArticleState
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


def create_test_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_create_user_article_state() -> None:
    """UserArticleState can be created for a user-article pair."""
    session = create_test_session()
    try:
        # Create user
        user = User(email="reader@example.com", password_hash="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create feed and article
        feed = Feed(url="https://example.com/rss", title="Example Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        article = Article(
            feed_id=feed.id,
            title="Test Article",
            url="https://example.com/article-1",
            guid="article-1",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Create state
        state = UserArticleState(user_id=user.id, article_id=article.id)
        session.add(state)
        session.commit()
        session.refresh(state)

        assert state.id is not None
        assert state.user_id == user.id
        assert state.article_id == article.id
        assert state.created_at is not None
        assert state.updated_at is not None
    finally:
        session.close()


def test_user_article_state_defaults_is_read_false() -> None:
    """is_read should default to False."""
    session = create_test_session()
    try:
        user = User(email="defaults@example.com", password_hash="hashed")
        session.add(user)
        session.commit()

        feed = Feed(url="https://defaults.com/rss", title="Defaults Feed")
        session.add(feed)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="Defaults Article",
            url="https://defaults.com/article-1",
            guid="defaults-1",
        )
        session.add(article)
        session.commit()

        state = UserArticleState(user_id=user.id, article_id=article.id)
        session.add(state)
        session.commit()
        session.refresh(state)

        assert state.is_read is False
    finally:
        session.close()


def test_user_article_state_defaults_is_saved_false() -> None:
    """is_saved should default to False."""
    session = create_test_session()
    try:
        user = User(email="saved@example.com", password_hash="hashed")
        session.add(user)
        session.commit()

        feed = Feed(url="https://saved.com/rss", title="Saved Feed")
        session.add(feed)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="Saved Article",
            url="https://saved.com/article-1",
            guid="saved-1",
        )
        session.add(article)
        session.commit()

        state = UserArticleState(user_id=user.id, article_id=article.id)
        session.add(state)
        session.commit()
        session.refresh(state)

        assert state.is_saved is False
    finally:
        session.close()


def test_user_article_state_uniqueness_constraint() -> None:
    """Duplicate (user_id, article_id) pairs should be rejected."""
    session = create_test_session()
    try:
        user = User(email="unique@example.com", password_hash="hashed")
        session.add(user)
        session.commit()

        feed = Feed(url="https://unique.com/rss", title="Unique Feed")
        session.add(feed)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="Unique Article",
            url="https://unique.com/article-1",
            guid="unique-1",
        )
        session.add(article)
        session.commit()

        # First state should succeed
        state1 = UserArticleState(user_id=user.id, article_id=article.id)
        session.add(state1)
        session.commit()

        # Second state with same user/article should fail
        state2 = UserArticleState(user_id=user.id, article_id=article.id)
        session.add(state2)

        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.close()


def test_user_article_state_read_at_nullable() -> None:
    """read_at should be nullable and can be set."""
    session = create_test_session()
    try:
        user = User(email="readat@example.com", password_hash="hashed")
        session.add(user)
        session.commit()

        feed = Feed(url="https://readat.com/rss", title="ReadAt Feed")
        session.add(feed)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="ReadAt Article",
            url="https://readat.com/article-1",
            guid="readat-1",
        )
        session.add(article)
        session.commit()

        # Create state without read_at
        state = UserArticleState(user_id=user.id, article_id=article.id)
        session.add(state)
        session.commit()
        session.refresh(state)

        assert state.read_at is None

        # Update with read_at
        now = datetime.now(UTC)
        state.is_read = True
        state.read_at = now
        session.commit()
        session.refresh(state)

        assert state.is_read is True
        assert state.read_at is not None
    finally:
        session.close()


def test_user_article_state_saved_at_nullable() -> None:
    """saved_at should be nullable and can be set."""
    session = create_test_session()
    try:
        user = User(email="savedat@example.com", password_hash="hashed")
        session.add(user)
        session.commit()

        feed = Feed(url="https://savedat.com/rss", title="SavedAt Feed")
        session.add(feed)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="SavedAt Article",
            url="https://savedat.com/article-1",
            guid="savedat-1",
        )
        session.add(article)
        session.commit()

        # Create state without saved_at
        state = UserArticleState(user_id=user.id, article_id=article.id)
        session.add(state)
        session.commit()
        session.refresh(state)

        assert state.saved_at is None

        # Update with saved_at
        now = datetime.now(UTC)
        state.is_saved = True
        state.saved_at = now
        session.commit()
        session.refresh(state)

        assert state.is_saved is True
        assert state.saved_at is not None
    finally:
        session.close()


def test_user_article_state_different_users_same_article() -> None:
    """Different users can have state for the same article."""
    session = create_test_session()
    try:
        user1 = User(email="user1@example.com", password_hash="hashed")
        user2 = User(email="user2@example.com", password_hash="hashed")
        session.add_all([user1, user2])
        session.commit()

        feed = Feed(url="https://multi.com/rss", title="Multi Feed")
        session.add(feed)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="Shared Article",
            url="https://multi.com/article-1",
            guid="multi-1",
        )
        session.add(article)
        session.commit()

        # Both users can have state for the same article
        state1 = UserArticleState(user_id=user1.id, article_id=article.id, is_read=True)
        state2 = UserArticleState(
            user_id=user2.id, article_id=article.id, is_read=False
        )
        session.add_all([state1, state2])
        session.commit()

        session.refresh(state1)
        session.refresh(state2)

        assert state1.is_read is True
        assert state2.is_read is False
    finally:
        session.close()


def test_user_article_state_same_user_different_articles() -> None:
    """Same user can have state for different articles."""
    session = create_test_session()
    try:
        user = User(email="multi-art@example.com", password_hash="hashed")
        session.add(user)
        session.commit()

        feed = Feed(url="https://multiart.com/rss", title="MultiArt Feed")
        session.add(feed)
        session.commit()

        article1 = Article(
            feed_id=feed.id,
            title="Article 1",
            url="https://multiart.com/article-1",
            guid="multiart-1",
        )
        article2 = Article(
            feed_id=feed.id,
            title="Article 2",
            url="https://multiart.com/article-2",
            guid="multiart-2",
        )
        session.add_all([article1, article2])
        session.commit()

        state1 = UserArticleState(
            user_id=user.id, article_id=article1.id, is_saved=True
        )
        state2 = UserArticleState(
            user_id=user.id, article_id=article2.id, is_saved=False
        )
        session.add_all([state1, state2])
        session.commit()

        session.refresh(state1)
        session.refresh(state2)

        assert state1.is_saved is True
        assert state2.is_saved is False
    finally:
        session.close()
