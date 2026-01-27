"""Service-layer logic for assigning feeds to collections."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.collection_feed import CollectionFeed
from app.models.feed import Feed
from app.models.user import User
from app.services.collections import get_collection


def assign_feed_to_collection(
    session: Session,
    user: User,
    collection_id: int,
    feed_id: int,
) -> tuple[CollectionFeed, bool]:
    """Assign a feed to a collection owned by the authenticated user.

    Args:
        session: Database session for persistence.
        user: Authenticated user requesting the assignment.
        collection_id: Collection identifier to attach the feed to.
        feed_id: Feed identifier to attach.

    Returns:
        tuple[CollectionFeed, bool]: Relationship and a created flag.

    Raises:
        HTTPException: If the collection or feed is not found.
    """
    collection = get_collection(session, user, collection_id)
    feed = session.get(Feed, feed_id)
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found.",
        )

    existing = session.execute(
        select(CollectionFeed).where(
            CollectionFeed.collection_id == collection.id,
            CollectionFeed.feed_id == feed.id,
        )
    ).scalar_one_or_none()
    if existing:
        # Idempotency: return existing relationship without duplicating.
        return existing, False

    link = CollectionFeed(collection_id=collection.id, feed_id=feed.id)
    session.add(link)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.execute(
            select(CollectionFeed).where(
                CollectionFeed.collection_id == collection.id,
                CollectionFeed.feed_id == feed.id,
            )
        ).scalar_one_or_none()
        if existing:
            # Idempotency: avoid failing if the link was created concurrently.
            return existing, False
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feed already assigned to collection.",
        ) from None
    session.refresh(link)
    return link, True


def unassign_feed_from_collection(
    session: Session,
    user: User,
    collection_id: int,
    feed_id: int,
) -> None:
    """Remove a feed assignment from a user-owned collection.

    Args:
        session: Database session for persistence.
        user: Authenticated user requesting the removal.
        collection_id: Collection identifier to detach from.
        feed_id: Feed identifier to remove.

    Raises:
        HTTPException: If the collection or feed is not found.
    """
    collection = get_collection(session, user, collection_id)
    feed = session.get(Feed, feed_id)
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found.",
        )

    existing = session.execute(
        select(CollectionFeed).where(
            CollectionFeed.collection_id == collection.id,
            CollectionFeed.feed_id == feed.id,
        )
    ).scalar_one_or_none()
    if not existing:
        # Idempotency: missing links are treated as already removed.
        return

    session.delete(existing)
    session.commit()


def list_collection_feeds(
    session: Session,
    user: User,
    collection_id: int,
) -> list[Feed]:
    """List all feeds assigned to a collection.

    Args:
        session: Database session for queries.
        user: Authenticated user requesting feeds.
        collection_id: Collection identifier.

    Returns:
        List of Feed objects assigned to the collection, ordered by title.

    Raises:
        HTTPException: If the collection is not found or not owned by the user.
    """
    # Verify ownership - raises 404 if not found or not owned
    get_collection(session, user, collection_id)

    # Query feeds via CollectionFeed join
    feeds = (
        session.execute(
            select(Feed)
            .join(CollectionFeed, Feed.id == CollectionFeed.feed_id)
            .where(CollectionFeed.collection_id == collection_id)
            .order_by(Feed.title.asc())
        )
        .scalars()
        .all()
    )

    return list(feeds)
