"""API routes for collection CRUD operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.collections import CollectionCreate, CollectionRead, CollectionUpdate
from app.services.auth import get_current_user
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
