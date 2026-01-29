"""API routes for Rule CRUD operations.

Provides endpoints for creating, listing, retrieving, updating, and
deleting rules. All operations are scoped to the authenticated user.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.rules import RuleCreate, RuleRead, RuleUpdate
from app.services.auth import get_current_user
from app.services.rules import (
    create_rule,
    delete_rule,
    get_rule,
    list_rules,
    update_rule,
)

router = APIRouter(prefix="/rules", tags=["rules"])
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule_route(
    rule_in: RuleCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> RuleRead:
    """Create a rule scoped to the authenticated user.

    Args:
        rule_in: Rule creation payload.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        RuleRead: Newly created rule.
    """
    return create_rule(session, current_user, rule_in)


@router.get("", response_model=list[RuleRead])
def list_rules_route(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[RuleRead]:
    """List rules owned by the authenticated user.

    Args:
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        list[RuleRead]: Rules owned by the user.
    """
    return list_rules(session, current_user)


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule_route(
    rule_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> RuleRead:
    """Retrieve a single rule by id.

    Args:
        rule_id: Rule identifier.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        RuleRead: Requested rule.

    Raises:
        HTTPException 404: Rule not found or not owned by user.
    """
    return get_rule(session, current_user, rule_id)


@router.patch("/{rule_id}", response_model=RuleRead)
def update_rule_route(
    rule_id: int,
    rule_in: RuleUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> RuleRead:
    """Update a rule owned by the authenticated user.

    Supports partial updates - only provided fields are modified.

    Args:
        rule_id: Rule identifier.
        rule_in: Rule update payload.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        RuleRead: Updated rule.

    Raises:
        HTTPException 404: Rule not found or not owned by user.
    """
    return update_rule(session, current_user, rule_id, rule_in)


@router.delete("/{rule_id}", response_model=RuleRead)
def delete_rule_route(
    rule_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> RuleRead:
    """Delete a rule owned by the authenticated user.

    Args:
        rule_id: Rule identifier.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        RuleRead: Deleted rule.

    Raises:
        HTTPException 404: Rule not found or not owned by user.
    """
    return delete_rule(session, current_user, rule_id)
