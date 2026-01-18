"""Tests for Phase 2 core aggregation models."""

from __future__ import annotations

import hashlib

import pytest
from app.db.base import Base
from app.models.article import Article
from app.models.collection import Collection
from app.models.collection_feed import CollectionFeed
from app.models.feed import Feed, normalize_url
from app.models.user import User
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


def create_test_session() -> Session:
    """Create an in-memory SQLite session with all tables created."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_phase2_tables_can_be_created() -> None:
    """Core aggregation tables should exist after metadata create_all."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    inspector = inspect(engine)

    expected_tables = {"collections", "feeds", "collection_feeds", "articles"}
    assert expected_tables.issubset(set(inspector.get_table_names()))


def test_feed_url_is_normalized_on_persist() -> None:
    """Feed URLs should be stored in canonical form."""
    session = create_test_session()
    try:
        feed = Feed(url="HTTP://Example.com/Feed/", title="Example Feed")
        session.add(feed)
        session.commit()
        session.refresh(feed)

        assert feed.url == "http://example.com/Feed"
    finally:
        session.close()


def test_feed_url_is_unique() -> None:
    """Feed URLs should be unique after normalization."""
    session = create_test_session()
    try:
        session.add(Feed(url="https://example.com/feed", title="Feed One"))
        session.commit()

        session.add(Feed(url="HTTPS://EXAMPLE.COM/feed", title="Feed Two"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_collection_feed_pair_is_unique() -> None:
    """Collection-to-feed mappings should not duplicate."""
    session = create_test_session()
    try:
        user = User(email="owner@example.com", password_hash="hash", is_active=True)
        feed = Feed(url="https://example.com/feed", title="Example Feed")
        session.add_all([user, feed])
        session.flush()

        collection = Collection(user_id=user.id, name="Research", description=None)
        session.add(collection)
        session.commit()

        mapping = CollectionFeed(collection_id=collection.id, feed_id=feed.id)
        session.add(mapping)
        session.commit()
        session.expunge(mapping)

        session.add(CollectionFeed(collection_id=collection.id, feed_id=feed.id))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_article_dedup_key_prefers_guid() -> None:
    """Articles should derive dedup_key from guid when available."""
    session = create_test_session()
    try:
        feed = Feed(url="https://example.com/feed", title="Example Feed")
        session.add(feed)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="Article",
            url="https://example.com/article",
            guid=" GUID-123 ",
        )
        session.add(article)
        session.commit()

        expected_key = hashlib.sha256(b"guid-123").hexdigest()
        assert article.dedup_key == expected_key
    finally:
        session.close()


def test_article_dedup_key_falls_back_to_url() -> None:
    """Articles should derive dedup_key from url when guid is missing."""
    session = create_test_session()
    try:
        feed = Feed(url="https://example.com/feed", title="Example Feed")
        session.add(feed)
        session.commit()

        article = Article(
            feed_id=feed.id,
            title="Article",
            url="HTTPS://Example.com/Article/",
            guid=None,
        )
        session.add(article)
        session.commit()

        normalized_url = normalize_url("HTTPS://Example.com/Article/")
        expected_key = hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()
        assert article.dedup_key == expected_key
    finally:
        session.close()
