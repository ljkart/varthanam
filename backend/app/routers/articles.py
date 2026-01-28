"""API routes for article state operations.

Provides endpoints for marking articles as read/unread and saved/unsaved.
All endpoints require authentication and operate on per-user state.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.user_article_state import UserArticleStateRead
from app.services.article_state import mark_read, mark_saved, mark_unread, mark_unsaved
from app.services.auth import get_current_user

router = APIRouter(prefix="/articles", tags=["articles"])
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.put("/{article_id}/read", response_model=UserArticleStateRead)
def mark_article_read(
    article_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> UserArticleStateRead:
    """Mark an article as read for the authenticated user.

    Creates a UserArticleState record if one doesn't exist.
    Idempotent: calling on already-read article preserves original read_at.

    Args:
        article_id: Article to mark as read.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        UserArticleStateRead: Updated state with is_read=true.

    Raises:
        HTTPException 404: Article not found.
    """
    return mark_read(session, current_user, article_id)


@router.delete("/{article_id}/read", response_model=UserArticleStateRead)
def mark_article_unread(
    article_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> UserArticleStateRead:
    """Mark an article as unread for the authenticated user.

    Creates a UserArticleState record if one doesn't exist.
    Idempotent: calling on already-unread article is a no-op.

    Args:
        article_id: Article to mark as unread.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        UserArticleStateRead: Updated state with is_read=false.

    Raises:
        HTTPException 404: Article not found.
    """
    return mark_unread(session, current_user, article_id)


@router.put("/{article_id}/saved", response_model=UserArticleStateRead)
def save_article(
    article_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> UserArticleStateRead:
    """Save an article for the authenticated user.

    Creates a UserArticleState record if one doesn't exist.
    Idempotent: calling on already-saved article preserves original saved_at.

    Args:
        article_id: Article to save.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        UserArticleStateRead: Updated state with is_saved=true.

    Raises:
        HTTPException 404: Article not found.
    """
    return mark_saved(session, current_user, article_id)


@router.delete("/{article_id}/saved", response_model=UserArticleStateRead)
def unsave_article(
    article_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> UserArticleStateRead:
    """Remove an article from the user's saved list.

    Creates a UserArticleState record if one doesn't exist.
    Idempotent: calling on already-unsaved article is a no-op.

    Args:
        article_id: Article to unsave.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        UserArticleStateRead: Updated state with is_saved=false.

    Raises:
        HTTPException 404: Article not found.
    """
    return mark_unsaved(session, current_user, article_id)
