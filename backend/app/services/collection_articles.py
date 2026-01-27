"""Service-layer logic for fetching articles from a collection."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.collection_feed import CollectionFeed
from app.models.user import User
from app.services.collections import get_collection


def list_collection_articles(
    session: Session,
    user: User,
    collection_id: int,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Article], int]:
    """Fetch paginated articles from all feeds assigned to a collection.

    Queries articles from all feeds linked to the collection via CollectionFeed.
    Results are sorted by published_at descending with nulls last, then by
    created_at descending as a tie-breaker for articles with the same or null
    published_at values.

    Ordering rationale:
    - published_at DESC: Show newest content first for relevance.
    - NULLS LAST: Articles without published dates appear after dated ones,
      since missing dates often indicate incomplete metadata.
    - created_at DESC tie-breaker: For articles with identical or null
      published_at, prefer recently fetched items.

    Args:
        session: Database session for queries.
        user: Authenticated user requesting articles.
        collection_id: Collection identifier.
        limit: Maximum number of articles to return (default 20).
        offset: Number of articles to skip for pagination (default 0).

    Returns:
        Tuple of (articles list, total count).

    Raises:
        HTTPException: If the collection is not found or not owned by the user.
    """
    # Verify ownership - raises 404 if not found or not owned
    get_collection(session, user, collection_id)

    # Build subquery for feed IDs in this collection
    feed_ids_subquery = (
        select(CollectionFeed.feed_id)
        .where(CollectionFeed.collection_id == collection_id)
        .subquery()
    )

    # Base query for articles in these feeds
    base_query = select(Article).where(Article.feed_id.in_(select(feed_ids_subquery)))

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total = session.execute(count_query).scalar_one()

    # Apply ordering: published_at DESC NULLS LAST, created_at DESC tie-breaker
    # Using nulls_last() to ensure articles without published dates appear after dated ones
    articles_query = (
        base_query.order_by(
            Article.published_at.desc().nulls_last(),
            Article.created_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    articles = session.execute(articles_query).scalars().all()

    return list(articles), total
