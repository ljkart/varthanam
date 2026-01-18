"""API routes for feed validation and creation."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.feeds import FeedCreate, FeedRead
from app.services.auth import get_current_user
from app.services.feeds import create_feed

router = APIRouter(prefix="/feeds", tags=["feeds"])
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=FeedRead, status_code=status.HTTP_201_CREATED)
def create_feed_route(
    feed_in: FeedCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> FeedRead:
    """Create a feed after validating the URL and parsed metadata.

    Args:
        feed_in: Feed creation payload.
        session: Database session dependency.
        current_user: Authenticated user.

    Returns:
        FeedRead: Newly created feed.
    """
    return create_feed(session, current_user, feed_in)
