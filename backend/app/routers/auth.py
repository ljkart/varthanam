"""API routes for registration and JWT authentication."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.settings import Settings, get_app_settings
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead
from app.services.auth import (
    authenticate_user,
    get_current_user,
    issue_access_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    session: SessionDep,
) -> UserRead:
    """Register a new user account.

    Args:
        user_in: Registration payload with email and password.
        session: Database session dependency.

    Returns:
        UserRead: The created user (safe fields only).
    """
    return register_user(session, user_in)


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    session: SessionDep,
    settings: SettingsDep,
) -> TokenResponse:
    """Authenticate a user and issue a JWT access token.

    Args:
        credentials: Login payload with email and password.
        session: Database session dependency.
        settings: Application settings with JWT configuration.

    Returns:
        TokenResponse: Bearer access token payload.
    """
    user = authenticate_user(session, credentials)
    access_token = issue_access_token(settings, user)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: CurrentUserDep,
) -> UserRead:
    """Return the authenticated user's safe profile.

    Args:
        current_user: Resolved user from the bearer token.

    Returns:
        UserRead: Current user safe fields.
    """
    return current_user
