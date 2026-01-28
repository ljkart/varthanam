"""Service-layer logic for fetching articles from a collection.

Supports filtering by user's read/saved state via optional parameters.
"""

from __future__ import annotations

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.collection_feed import CollectionFeed
from app.models.user import User
from app.models.user_article_state import UserArticleState
from app.services.collections import get_collection


def list_collection_articles(
    session: Session,
    user: User,
    collection_id: int,
    *,
    limit: int = 20,
    offset: int = 0,
    unread_only: bool = False,
    saved_only: bool = False,
) -> tuple[list[Article], int]:
    """Fetch paginated articles from all feeds assigned to a collection.

    Queries articles from all feeds linked to the collection via CollectionFeed.
    Results are sorted by published_at descending with nulls last, then by
    created_at descending as a tie-breaker for articles with the same or null
    published_at values.

    Filter behavior:
    - unread_only=True: Returns articles where the user has no state row
      (treated as unread) OR state.is_read=False. Uses LEFT OUTER JOIN to
      include articles without state rows.
    - saved_only=True: Returns articles where state row exists AND is_saved=True.
      Uses INNER JOIN since we only want articles with explicit saved state.
    - Both filters: Returns intersection (unread AND saved articles).

    Unread semantics rationale:
    - Articles without a UserArticleState row are treated as unread because
      state rows are only created when a user explicitly interacts with an
      article. This avoids pre-creating state rows for all user-article pairs.

    Join type rationale:
    - LEFT OUTER JOIN for unread: Includes articles with missing state rows
      (which are implicitly unread).
    - When saved_only is requested without unread_only, we use INNER JOIN
      because saved articles must have an explicit state row with is_saved=True.
    - When both filters are combined, we use LEFT OUTER JOIN but filter for
      (state is NULL OR is_read=False) AND (is_saved=True), which effectively
      requires a state row for the saved condition.

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
        unread_only: If True, only return unread articles (default False).
        saved_only: If True, only return saved articles (default False).

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

    # Build the query based on filter requirements
    if unread_only or saved_only:
        # We need to join with UserArticleState for filtering
        base_query = _build_filtered_query(
            user.id,
            feed_ids_subquery,
            unread_only=unread_only,
            saved_only=saved_only,
        )
    else:
        # No filters - simple query without join
        base_query = select(Article).where(
            Article.feed_id.in_(select(feed_ids_subquery))
        )

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


def _build_filtered_query(
    user_id: int,
    feed_ids_subquery,
    *,
    unread_only: bool,
    saved_only: bool,
):
    """Build a filtered query for articles based on user state.

    This helper constructs the appropriate SQL query with joins and filters
    based on the requested filter combination.

    Args:
        user_id: ID of the authenticated user.
        feed_ids_subquery: Subquery containing feed IDs in the collection.
        unread_only: Filter for unread articles.
        saved_only: Filter for saved articles.

    Returns:
        SQLAlchemy select statement for filtered articles.
    """
    # Build filter conditions
    filters = []

    if saved_only and not unread_only:
        # saved_only without unread_only: Use INNER JOIN since we require
        # an explicit state row with is_saved=True
        query = (
            select(Article)
            .join(
                UserArticleState,
                and_(
                    UserArticleState.article_id == Article.id,
                    UserArticleState.user_id == user_id,
                ),
            )
            .where(Article.feed_id.in_(select(feed_ids_subquery)))
            .where(UserArticleState.is_saved == True)  # noqa: E712
        )
        return query

    # For unread_only (with or without saved_only), use LEFT OUTER JOIN
    # to include articles without state rows (treated as unread)
    query = (
        select(Article)
        .outerjoin(
            UserArticleState,
            and_(
                UserArticleState.article_id == Article.id,
                UserArticleState.user_id == user_id,
            ),
        )
        .where(Article.feed_id.in_(select(feed_ids_subquery)))
    )

    if unread_only:
        # Unread: no state row (NULL) OR is_read=False
        filters.append(
            or_(
                UserArticleState.id == None,  # noqa: E711 - SQLAlchemy requires == None
                UserArticleState.is_read == False,  # noqa: E712
            )
        )

    if saved_only:
        # Saved requires explicit state row with is_saved=True
        # Note: This effectively requires a state row, so combined with unread_only,
        # we get articles that are unread (is_read=False, not NULL) AND saved
        filters.append(UserArticleState.is_saved == True)  # noqa: E712

    if filters:
        query = query.where(and_(*filters))

    return query
