"""Service-layer logic for Rule CRUD operations.

All operations are scoped to the authenticated user for access control.
Users can only view, modify, and delete their own rules.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rule import Rule
from app.models.user import User
from app.schemas.rules import RuleCreate, RuleUpdate


def _get_rule_for_user(
    session: Session,
    user_id: int,
    rule_id: int,
) -> Rule | None:
    """Fetch a rule scoped to a user for access control.

    Access control rationale:
    - We scope the query by user_id to prevent accessing other users' rules.
    - If the rule belongs to another user, we return None rather than
      raising a 403, to avoid leaking information about rule existence.

    Args:
        session: Database session for queries.
        user_id: Authenticated user's ID.
        rule_id: Rule identifier to fetch.

    Returns:
        Rule if found and owned by user, None otherwise.
    """
    return session.execute(
        select(Rule).where(
            Rule.id == rule_id,
            Rule.user_id == user_id,
        )
    ).scalar_one_or_none()


def create_rule(
    session: Session,
    user: User,
    rule_in: RuleCreate,
) -> Rule:
    """Create a rule owned by the authenticated user.

    Args:
        session: Database session for persistence.
        user: Authenticated user creating the rule.
        rule_in: Input payload with rule fields.

    Returns:
        Rule: Newly created rule record.
    """
    rule = Rule(
        user_id=user.id,
        name=rule_in.name,
        frequency_minutes=rule_in.frequency_minutes,
        include_keywords=rule_in.include_keywords,
        exclude_keywords=rule_in.exclude_keywords,
        collection_id=rule_in.collection_id,
        is_active=rule_in.is_active,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def list_rules(session: Session, user: User) -> list[Rule]:
    """Return all rules for the authenticated user.

    Args:
        session: Database session for queries.
        user: Authenticated user requesting rules.

    Returns:
        list[Rule]: Ordered rules owned by the user.
    """
    return list(
        session.execute(
            select(Rule).where(Rule.user_id == user.id).order_by(Rule.created_at.asc())
        )
        .scalars()
        .all()
    )


def get_rule(session: Session, user: User, rule_id: int) -> Rule:
    """Fetch a single rule scoped to the authenticated user.

    Args:
        session: Database session for queries.
        user: Authenticated user requesting the rule.
        rule_id: Rule identifier.

    Returns:
        Rule: Matching rule record.

    Raises:
        HTTPException: 404 if the rule does not exist or is not owned by user.
    """
    rule = _get_rule_for_user(session, user.id, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found.",
        )
    return rule


def update_rule(
    session: Session,
    user: User,
    rule_id: int,
    rule_in: RuleUpdate,
) -> Rule:
    """Update a rule owned by the authenticated user.

    Supports partial updates - only provided fields are modified.

    Args:
        session: Database session for persistence.
        user: Authenticated user updating the rule.
        rule_id: Rule identifier.
        rule_in: Update payload containing modified fields.

    Returns:
        Rule: Updated rule record.

    Raises:
        HTTPException: 404 if the rule is not found or not owned by user.
    """
    rule = get_rule(session, user, rule_id)
    fields_set = rule_in.model_fields_set

    if "name" in fields_set and rule_in.name is not None:
        rule.name = rule_in.name

    if "frequency_minutes" in fields_set and rule_in.frequency_minutes is not None:
        rule.frequency_minutes = rule_in.frequency_minutes

    if "include_keywords" in fields_set:
        rule.include_keywords = rule_in.include_keywords

    if "exclude_keywords" in fields_set:
        rule.exclude_keywords = rule_in.exclude_keywords

    if "collection_id" in fields_set:
        rule.collection_id = rule_in.collection_id

    if "is_active" in fields_set and rule_in.is_active is not None:
        rule.is_active = rule_in.is_active

    session.commit()
    session.refresh(rule)
    return rule


def delete_rule(
    session: Session,
    user: User,
    rule_id: int,
) -> Rule:
    """Delete a rule owned by the authenticated user.

    Note: Related RuleMatch records will be handled by the database
    cascade behavior if configured, or will become orphaned.

    Args:
        session: Database session for deletion.
        user: Authenticated user deleting the rule.
        rule_id: Rule identifier.

    Returns:
        Rule: Deleted rule record (for response).

    Raises:
        HTTPException: 404 if the rule is not found or not owned by user.
    """
    rule = get_rule(session, user, rule_id)
    session.delete(rule)
    session.commit()
    return rule
