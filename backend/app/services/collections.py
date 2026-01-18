"""Service-layer logic for collection CRUD operations."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collection import Collection
from app.models.user import User
from app.schemas.collections import CollectionCreate, CollectionUpdate


def _get_collection_for_user(
    session: Session,
    user_id: int,
    collection_id: int,
) -> Collection | None:
    """Fetch a collection scoped to a user for access control."""
    # Scope by user_id to avoid leaking whether another user's collection exists.
    return session.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
    ).scalar_one_or_none()


def _ensure_unique_name(
    session: Session,
    user_id: int,
    name: str,
    *,
    exclude_collection_id: int | None = None,
) -> None:
    """Ensure the collection name is unique for the given user.

    Args:
        session: Database session for lookups.
        user_id: Owner id for scoping uniqueness.
        name: Proposed collection name.
        exclude_collection_id: Optional collection id to exclude when updating.

    Raises:
        HTTPException: If the name already exists for this user.
    """
    query = select(Collection).where(
        Collection.user_id == user_id,
        Collection.name == name,
    )
    if exclude_collection_id is not None:
        query = query.where(Collection.id != exclude_collection_id)
    existing = session.execute(query).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Collection name already exists.",
        )


def create_collection(
    session: Session,
    user: User,
    collection_in: CollectionCreate,
) -> Collection:
    """Create a collection owned by the authenticated user.

    Args:
        session: Database session for persistence.
        user: Authenticated user creating the collection.
        collection_in: Input payload with collection fields.

    Returns:
        Collection: Newly created collection record.

    Raises:
        HTTPException: If the name already exists for the user.
    """
    _ensure_unique_name(session, user.id, collection_in.name)

    collection = Collection(
        user_id=user.id,
        name=collection_in.name,
        description=collection_in.description,
    )
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


def list_collections(session: Session, user: User) -> list[Collection]:
    """Return all collections for the authenticated user.

    Args:
        session: Database session for queries.
        user: Authenticated user requesting collections.

    Returns:
        list[Collection]: Ordered collections owned by the user.
    """
    return (
        session.execute(
            select(Collection)
            .where(Collection.user_id == user.id)
            .order_by(Collection.created_at.asc())
        )
        .scalars()
        .all()
    )


def get_collection(session: Session, user: User, collection_id: int) -> Collection:
    """Fetch a single collection scoped to the authenticated user.

    Args:
        session: Database session for queries.
        user: Authenticated user requesting the collection.
        collection_id: Collection identifier.

    Returns:
        Collection: Matching collection record.

    Raises:
        HTTPException: If the collection does not exist for the user.
    """
    collection = _get_collection_for_user(session, user.id, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found.",
        )
    return collection


def update_collection(
    session: Session,
    user: User,
    collection_id: int,
    collection_in: CollectionUpdate,
) -> Collection:
    """Update a collection owned by the authenticated user.

    Args:
        session: Database session for persistence.
        user: Authenticated user updating the collection.
        collection_id: Collection identifier.
        collection_in: Update payload containing modified fields.

    Returns:
        Collection: Updated collection record.

    Raises:
        HTTPException: If the collection is not found or name conflicts.
    """
    collection = get_collection(session, user, collection_id)
    fields_set = collection_in.model_fields_set

    if "name" in fields_set and collection_in.name is not None:
        _ensure_unique_name(
            session,
            user.id,
            collection_in.name,
            exclude_collection_id=collection.id,
        )
        collection.name = collection_in.name

    if "description" in fields_set:
        collection.description = collection_in.description

    session.commit()
    session.refresh(collection)
    return collection


def delete_collection(
    session: Session,
    user: User,
    collection_id: int,
) -> Collection:
    """Delete a collection owned by the authenticated user.

    Args:
        session: Database session for deletion.
        user: Authenticated user deleting the collection.
        collection_id: Collection identifier.

    Returns:
        Collection: Deleted collection record.

    Raises:
        HTTPException: If the collection is not found for the user.
    """
    collection = get_collection(session, user, collection_id)
    session.delete(collection)
    session.commit()
    return collection
