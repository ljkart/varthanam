"""Service-layer logic for user article state operations.

Handles marking articles as read/unread and saved/unsaved for authenticated users.
All operations are idempotent and per-user scoped.

Timestamp behavior:
- mark_read: Sets is_read=true, read_at=now (only on transition from unread)
- mark_unread: Sets is_read=false, read_at=NULL
- mark_saved: Sets is_saved=true, saved_at=now (only on transition from unsaved)
- mark_unsaved: Sets is_saved=false, saved_at=NULL
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.user import User
from app.models.user_article_state import UserArticleState


def _get_article_or_404(session: Session, article_id: int) -> Article:
    """Fetch an article by ID or raise 404 if not found.

    Args:
        session: Database session for queries.
        article_id: Article ID to fetch.

    Returns:
        Article: The requested article.

    Raises:
        HTTPException: 404 if article does not exist.
    """
    article = session.execute(
        select(Article).where(Article.id == article_id)
    ).scalar_one_or_none()
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    return article


def _get_or_create_state(
    session: Session,
    user_id: int,
    article_id: int,
) -> UserArticleState:
    """Get existing state or create a new one for user-article pair.

    Args:
        session: Database session.
        user_id: Authenticated user's ID.
        article_id: Article ID (must exist).

    Returns:
        UserArticleState: Existing or newly created state record.
    """
    state = session.execute(
        select(UserArticleState).where(
            UserArticleState.user_id == user_id,
            UserArticleState.article_id == article_id,
        )
    ).scalar_one_or_none()

    if state is None:
        state = UserArticleState(user_id=user_id, article_id=article_id)
        session.add(state)
        session.flush()  # Assign ID without committing

    return state


def mark_read(session: Session, user: User, article_id: int) -> UserArticleState:
    """Mark an article as read for the authenticated user.

    Creates a UserArticleState record if one doesn't exist.
    Idempotent: calling on already-read article preserves original read_at.

    Args:
        session: Database session.
        user: Authenticated user.
        article_id: Article to mark as read.

    Returns:
        UserArticleState: Updated state record.

    Raises:
        HTTPException: 404 if article does not exist.
    """
    _get_article_or_404(session, article_id)
    state = _get_or_create_state(session, user.id, article_id)

    # Only set read_at on transition from unread to read
    if not state.is_read:
        state.is_read = True
        state.read_at = datetime.now(UTC)

    session.commit()
    session.refresh(state)
    return state


def mark_unread(session: Session, user: User, article_id: int) -> UserArticleState:
    """Mark an article as unread for the authenticated user.

    Creates a UserArticleState record if one doesn't exist.
    Idempotent: calling on already-unread article is a no-op.

    Args:
        session: Database session.
        user: Authenticated user.
        article_id: Article to mark as unread.

    Returns:
        UserArticleState: Updated state record.

    Raises:
        HTTPException: 404 if article does not exist.
    """
    _get_article_or_404(session, article_id)
    state = _get_or_create_state(session, user.id, article_id)

    state.is_read = False
    state.read_at = None

    session.commit()
    session.refresh(state)
    return state


def mark_saved(session: Session, user: User, article_id: int) -> UserArticleState:
    """Save an article for the authenticated user.

    Creates a UserArticleState record if one doesn't exist.
    Idempotent: calling on already-saved article preserves original saved_at.

    Args:
        session: Database session.
        user: Authenticated user.
        article_id: Article to save.

    Returns:
        UserArticleState: Updated state record.

    Raises:
        HTTPException: 404 if article does not exist.
    """
    _get_article_or_404(session, article_id)
    state = _get_or_create_state(session, user.id, article_id)

    # Only set saved_at on transition from unsaved to saved
    if not state.is_saved:
        state.is_saved = True
        state.saved_at = datetime.now(UTC)

    session.commit()
    session.refresh(state)
    return state


def mark_unsaved(session: Session, user: User, article_id: int) -> UserArticleState:
    """Remove an article from the user's saved list.

    Creates a UserArticleState record if one doesn't exist.
    Idempotent: calling on already-unsaved article is a no-op.

    Args:
        session: Database session.
        user: Authenticated user.
        article_id: Article to unsave.

    Returns:
        UserArticleState: Updated state record.

    Raises:
        HTTPException: 404 if article does not exist.
    """
    _get_article_or_404(session, article_id)
    state = _get_or_create_state(session, user.id, article_id)

    state.is_saved = False
    state.saved_at = None

    session.commit()
    session.refresh(state)
    return state
