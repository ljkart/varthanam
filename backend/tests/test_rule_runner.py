"""Unit tests for rule execution worker.

Tests cover:
- Matching stores RuleMatch rows correctly
- Running twice does not create duplicates (idempotent)
- Exclude/include semantics respected
- Collection scope respected
- last_run_at updated after successful run
- Missing rule handling
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.db.base import Base
from app.models.article import Article
from app.models.collection import Collection
from app.models.collection_feed import CollectionFeed
from app.models.feed import Feed
from app.models.rule import Rule
from app.models.rule_match import RuleMatch
from app.models.user import User
from app.workers.rule_runner import RuleNotFoundError, run_rule
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


def create_feed(
    session: Session,
    url: str = "https://example.com/feed.xml",
    title: str = "Test Feed",
) -> Feed:
    """Create a test feed."""
    feed = Feed(url=url, title=title)
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


def create_collection(
    session: Session, user: User, name: str = "Test Collection"
) -> Collection:
    """Create a test collection."""
    collection = Collection(user_id=user.id, name=name)
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


def create_article(
    session: Session,
    feed: Feed,
    title: str,
    summary: str | None = None,
    content: str | None = None,
    guid: str | None = None,
) -> Article:
    """Create an article."""
    article = Article(
        feed_id=feed.id,
        title=title,
        summary=summary,
        content=content,
        guid=guid or f"guid-{title.lower().replace(' ', '-')}",
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
    include_keywords: str | None = None,
    exclude_keywords: str | None = None,
    collection_id: int | None = None,
    frequency_minutes: int = 60,
) -> Rule:
    """Create a rule."""
    rule = Rule(
        user_id=user.id,
        name=name,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        collection_id=collection_id,
        frequency_minutes=frequency_minutes,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


# --- Basic matching tests ---


class TestRunRuleBasicMatching:
    """Tests for basic rule matching and RuleMatch creation."""

    def test_matching_article_creates_rule_match(self):
        """Articles matching include keywords should create RuleMatch rows."""
        session = create_test_session()
        try:
            user = create_user(session, "match@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)

            matching_article = create_article(
                session, feed, "Python Tutorial", summary="Learn Python programming"
            )
            # Non-matching article (intentionally not used in assertions)
            create_article(
                session, feed, "JavaScript Guide", summary="Learn JavaScript"
            )

            rule = create_rule(session, user, "Python Rule", include_keywords="python")

            result = run_rule(rule.id, session)

            matches = session.query(RuleMatch).filter_by(rule_id=rule.id).all()
            assert len(matches) == 1
            assert matches[0].article_id == matching_article.id
            assert matches[0].matched_at is not None

            assert result.candidates == 2
            assert result.matched == 1
            assert result.created == 1
            assert result.skipped == 0
        finally:
            session.close()

    def test_exclude_keyword_prevents_match(self):
        """Articles matching exclude keywords should not create RuleMatch."""
        session = create_test_session()
        try:
            user = create_user(session, "exclude@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)

            # Article matches include but also matches exclude
            create_article(
                session,
                feed,
                "Python for Beginners",
                summary="A beginner guide to Python",
            )

            rule = create_rule(
                session,
                user,
                "Advanced Python Only",
                include_keywords="python",
                exclude_keywords="beginner",
            )

            result = run_rule(rule.id, session)

            matches = session.query(RuleMatch).filter_by(rule_id=rule.id).all()
            assert len(matches) == 0
            assert result.matched == 0
        finally:
            session.close()

    def test_no_include_keywords_matches_all_except_excluded(self):
        """Rule with no include keywords matches all articles (except excluded)."""
        session = create_test_session()
        try:
            user = create_user(session, "all@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)

            article1 = create_article(session, feed, "Tech News")
            article2 = create_article(session, feed, "Spam Article")
            article3 = create_article(session, feed, "Science Update")

            rule = create_rule(
                session,
                user,
                "All except spam",
                include_keywords=None,
                exclude_keywords="spam",
            )

            run_rule(rule.id, session)

            matches = session.query(RuleMatch).filter_by(rule_id=rule.id).all()
            matched_article_ids = {m.article_id for m in matches}

            assert len(matches) == 2
            assert article1.id in matched_article_ids
            assert article2.id not in matched_article_ids  # Excluded
            assert article3.id in matched_article_ids
        finally:
            session.close()


# --- Idempotency tests ---


class TestRunRuleIdempotency:
    """Tests for idempotent rule execution."""

    def test_running_twice_does_not_duplicate_matches(self):
        """Running the same rule twice should not create duplicate RuleMatch rows."""
        session = create_test_session()
        try:
            user = create_user(session, "idempotent@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)

            create_article(session, feed, "Python Tips", summary="Great Python tips")

            rule = create_rule(session, user, "Python Rule", include_keywords="python")

            # First run
            result1 = run_rule(rule.id, session)
            assert result1.created == 1
            assert result1.skipped == 0

            # Second run - should skip existing match
            result2 = run_rule(rule.id, session)
            assert result2.created == 0
            assert result2.skipped == 1
            assert result2.matched == 1  # Still matches, just not created

            # Verify only one RuleMatch exists
            matches = session.query(RuleMatch).filter_by(rule_id=rule.id).all()
            assert len(matches) == 1
        finally:
            session.close()

    def test_new_articles_matched_on_rerun(self):
        """New articles should be matched when rule is run again."""
        session = create_test_session()
        try:
            user = create_user(session, "rerun@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)

            # First article
            create_article(session, feed, "Python Basics", summary="Learn Python")

            rule = create_rule(session, user, "Python Rule", include_keywords="python")

            # First run
            result1 = run_rule(rule.id, session)
            assert result1.created == 1

            # Add new article
            create_article(
                session, feed, "Python Advanced", summary="Advanced Python topics"
            )

            # Second run - should pick up new article
            result2 = run_rule(rule.id, session)
            assert result2.created == 1  # New article
            assert result2.skipped == 1  # Existing article

            matches = session.query(RuleMatch).filter_by(rule_id=rule.id).all()
            assert len(matches) == 2
        finally:
            session.close()


# --- Collection scope tests ---


class TestRunRuleCollectionScope:
    """Tests for collection-scoped rule execution."""

    def test_collection_scoped_rule_only_matches_collection_articles(self):
        """Rule with collection_id only matches articles from that collection's feeds."""
        session = create_test_session()
        try:
            user = create_user(session, "scope@example.com")

            feed1 = create_feed(session, "https://tech.com/feed.xml", "Tech Feed")
            feed2 = create_feed(session, "https://science.com/feed.xml", "Science Feed")

            collection1 = create_collection(session, user, "Tech News")
            collection2 = create_collection(session, user, "Science News")

            link_feed_to_collection(session, collection1, feed1)
            link_feed_to_collection(session, collection2, feed2)

            # Create articles in both feeds
            article_in_scope = create_article(
                session, feed1, "Python in Tech", summary="Python article"
            )
            # Out-of-scope article (should not be matched)
            create_article(
                session, feed2, "Python in Science", summary="Python article"
            )

            # Rule scoped to collection1
            rule = create_rule(
                session,
                user,
                "Tech Python",
                include_keywords="python",
                collection_id=collection1.id,
            )

            result = run_rule(rule.id, session)

            matches = session.query(RuleMatch).filter_by(rule_id=rule.id).all()
            assert len(matches) == 1
            assert matches[0].article_id == article_in_scope.id

            # Verify counters - only in-scope articles are candidates
            assert result.candidates == 1
            assert result.matched == 1
        finally:
            session.close()

    def test_unscoped_rule_matches_all_user_articles(self):
        """Rule without collection_id matches articles from all user's collections."""
        session = create_test_session()
        try:
            user = create_user(session, "unscoped@example.com")

            feed1 = create_feed(session, "https://tech.com/feed.xml", "Tech Feed")
            feed2 = create_feed(session, "https://science.com/feed.xml", "Science Feed")

            collection1 = create_collection(session, user, "Tech News")
            collection2 = create_collection(session, user, "Science News")

            link_feed_to_collection(session, collection1, feed1)
            link_feed_to_collection(session, collection2, feed2)

            article1 = create_article(
                session, feed1, "Python Tech", summary="Python in tech"
            )
            article2 = create_article(
                session, feed2, "Python Science", summary="Python in science"
            )

            # Rule without collection scope
            rule = create_rule(
                session,
                user,
                "All Python",
                include_keywords="python",
                collection_id=None,
            )

            run_rule(rule.id, session)

            matches = session.query(RuleMatch).filter_by(rule_id=rule.id).all()
            matched_ids = {m.article_id for m in matches}

            assert len(matches) == 2
            assert article1.id in matched_ids
            assert article2.id in matched_ids
        finally:
            session.close()

    def test_unscoped_rule_does_not_match_other_users_articles(self):
        """Unscoped rule should NOT match articles from other users' collections."""
        session = create_test_session()
        try:
            user1 = create_user(session, "user1@example.com")
            user2 = create_user(session, "user2@example.com")

            # User 1's feed and collection
            feed1 = create_feed(session, "https://user1.com/feed.xml", "User1 Feed")
            collection1 = create_collection(session, user1, "User1 Collection")
            link_feed_to_collection(session, collection1, feed1)
            article1 = create_article(
                session, feed1, "Python for User1", summary="Python article"
            )

            # User 2's feed and collection
            feed2 = create_feed(session, "https://user2.com/feed.xml", "User2 Feed")
            collection2 = create_collection(session, user2, "User2 Collection")
            link_feed_to_collection(session, collection2, feed2)
            _article2 = create_article(
                session, feed2, "Python for User2", summary="Python article"
            )

            # User 1's unscoped rule - should only match user1's articles
            rule = create_rule(
                session,
                user1,
                "User1 Python",
                include_keywords="python",
                collection_id=None,
            )

            result = run_rule(rule.id, session)

            matches = session.query(RuleMatch).filter_by(rule_id=rule.id).all()
            matched_ids = {m.article_id for m in matches}

            # Should only match user1's article, not user2's
            assert len(matches) == 1
            assert article1.id in matched_ids
            assert result.candidates == 1  # Only user1's article is a candidate
        finally:
            session.close()


# --- last_run_at update tests ---


class TestRunRuleLastRunAt:
    """Tests for last_run_at timestamp updates."""

    def test_last_run_at_updated_after_successful_run(self):
        """last_run_at should be updated after successful rule execution."""
        session = create_test_session()
        try:
            user = create_user(session, "timestamp@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)
            create_article(session, feed, "Any Article")

            rule = create_rule(session, user, "Test Rule", include_keywords=None)

            assert rule.last_run_at is None

            before_run = datetime.now(UTC)
            run_rule(rule.id, session)
            after_run = datetime.now(UTC)

            session.refresh(rule)
            assert rule.last_run_at is not None
            # SQLite returns timezone-naive datetimes, so we compare without tz
            last_run_naive = rule.last_run_at.replace(tzinfo=None)
            before_naive = before_run.replace(tzinfo=None)
            after_naive = after_run.replace(tzinfo=None)
            assert before_naive <= last_run_naive <= after_naive
        finally:
            session.close()

    def test_last_run_at_updated_even_with_no_matches(self):
        """last_run_at should be updated even if no articles match."""
        session = create_test_session()
        try:
            user = create_user(session, "nomatch@example.com")
            feed = create_feed(session)
            collection = create_collection(session, user)
            link_feed_to_collection(session, collection, feed)
            create_article(session, feed, "JavaScript Article")

            rule = create_rule(session, user, "Python Only", include_keywords="python")

            result = run_rule(rule.id, session)

            session.refresh(rule)
            assert rule.last_run_at is not None
            assert result.matched == 0
        finally:
            session.close()


# --- Error handling tests ---


class TestRunRuleErrorHandling:
    """Tests for error handling."""

    def test_missing_rule_raises_exception(self):
        """Running a non-existent rule should raise RuleNotFoundError."""
        session = create_test_session()
        try:
            with pytest.raises(RuleNotFoundError) as exc_info:
                run_rule(99999, session)

            assert "Rule with id 99999 not found" in str(exc_info.value)
        finally:
            session.close()

    def test_empty_candidate_set_succeeds(self):
        """Rule should succeed even with no candidate articles."""
        session = create_test_session()
        try:
            user = create_user(session, "empty@example.com")
            collection = create_collection(session, user)
            # Collection has no feeds/articles

            rule = create_rule(
                session,
                user,
                "Empty Rule",
                include_keywords="python",
                collection_id=collection.id,
            )

            result = run_rule(rule.id, session)

            assert result.candidates == 0
            assert result.matched == 0
            assert result.created == 0

            # last_run_at still updated
            session.refresh(rule)
            assert rule.last_run_at is not None
        finally:
            session.close()
