"""API routes for collection CRUD operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.articles import PaginatedArticlesResponse
from app.schemas.collections import (
    CollectionCreate,
    CollectionFeedCreate,
    CollectionFeedRead,
    CollectionRead,
    CollectionUpdate,
)
from app.services.auth import get_current_user
from app.services.collection_articles import list_collection_articles
from app.services.collection_feeds import (
    assign_feed_to_collection,
    unassign_feed_from_collection,
)
from app.services.collections import (
    create_collection,
    delete_collection,
    get_collection,
    list_collections,
    update_collection,
)

router = APIRouter(prefix="/collections", tags=["collections"])
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
def create_collection_route(
    collection_in: CollectionCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CollectionRead:
    """Create a collection scoped to the authenticated user.

    Args:
        collection_in: Collection creation payload.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        CollectionRead: Newly created collection.
    """
    return create_collection(session, current_user, collection_in)


@router.get("", response_model=list[CollectionRead])
def list_collections_route(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[CollectionRead]:
    """List collections owned by the authenticated user.

    Args:
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        list[CollectionRead]: Collections owned by the user.
    """
    return list_collections(session, current_user)


@router.get("/{collection_id}", response_model=CollectionRead)
def get_collection_route(
    collection_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CollectionRead:
    """Retrieve a single collection by id.

    Args:
        collection_id: Collection identifier.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        CollectionRead: Requested collection.
    """
    return get_collection(session, current_user, collection_id)


@router.patch("/{collection_id}", response_model=CollectionRead)
def update_collection_route(
    collection_id: int,
    collection_in: CollectionUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CollectionRead:
    """Update a collection owned by the authenticated user.

    Args:
        collection_id: Collection identifier.
        collection_in: Collection update payload.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        CollectionRead: Updated collection.
    """
    return update_collection(session, current_user, collection_id, collection_in)


@router.delete("/{collection_id}", response_model=CollectionRead)
def delete_collection_route(
    collection_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CollectionRead:
    """Delete a collection owned by the authenticated user.

    Args:
        collection_id: Collection identifier.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        CollectionRead: Deleted collection.
    """
    return delete_collection(session, current_user, collection_id)


@router.get(
    "/{collection_id}/articles",
    response_model=PaginatedArticlesResponse,
)
def list_collection_articles_route(
    collection_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(default=20, ge=1, le=100, description="Max items per page"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    unread_only: bool = Query(
        default=False,
        description="Filter to only unread articles (no state row or is_read=false)",
    ),
    saved_only: bool = Query(
        default=False,
        description="Filter to only saved articles (is_saved=true)",
    ),
) -> PaginatedArticlesResponse:
    """List articles from all feeds in a collection with pagination and filters.

    Returns a merged list of articles from all feeds assigned to the collection,
    sorted by published_at descending (nulls last), with created_at as tie-breaker.

    Filter behavior:
    - unread_only=true: Returns articles with no state row (treated as unread)
      or is_read=false.
    - saved_only=true: Returns articles with is_saved=true.
    - Both filters: Returns intersection (unread AND saved).

    Args:
        collection_id: Collection identifier.
        session: Database session dependency.
        current_user: Authenticated user.
        limit: Maximum items to return (1-100, default 20).
        offset: Number of items to skip (default 0).
        unread_only: Filter for unread articles only (default false).
        saved_only: Filter for saved articles only (default false).

    Returns:
        PaginatedArticlesResponse: Articles with pagination metadata.
    """
    articles, total = list_collection_articles(
        session,
        current_user,
        collection_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
        saved_only=saved_only,
    )
    return PaginatedArticlesResponse(
        items=articles,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{collection_id}/feeds",
    response_model=CollectionFeedRead,
    status_code=status.HTTP_201_CREATED,
)
def assign_feed_to_collection_route(
    collection_id: int,
    assignment_in: CollectionFeedCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
    response: Response,
) -> CollectionFeedRead:
    """Assign a feed to a collection owned by the authenticated user.

    Args:
        collection_id: Collection identifier to attach the feed to.
        assignment_in: Payload containing the feed identifier.
        session: Database session dependency.
        current_user: Authenticated user.
        response: Response object for adjusting status codes.

    Returns:
        CollectionFeedRead: Relationship payload for the assignment.
    """
    link, created = assign_feed_to_collection(
        session,
        current_user,
        collection_id,
        assignment_in.feed_id,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return link


@router.delete(
    "/{collection_id}/feeds/{feed_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_feed_from_collection_route(
    collection_id: int,
    feed_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> None:
    """Remove a feed assignment from a collection owned by the user.

    Args:
        collection_id: Collection identifier to detach from.
        feed_id: Feed identifier to remove.
        session: Database session dependency.
        current_user: Authenticated user.
    """
    unassign_feed_from_collection(session, current_user, collection_id, feed_id)
