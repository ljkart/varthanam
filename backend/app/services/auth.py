"""Service-layer logic for authentication and JWT validation."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.core.settings import Settings, get_app_settings
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
TokenDep = Annotated[str, Depends(_oauth2_scheme)]
SessionDep = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]


def register_user(session: Session, user_in: UserCreate) -> User:
    """Register a new user, ensuring email uniqueness.

    Args:
        session: Database session for persistence.
        user_in: Registration payload containing email and password.

    Returns:
        User: Newly created user record.

    Raises:
        HTTPException: If the email address is already registered.
    """
    existing_user = session.execute(
        select(User).where(User.email == user_in.email)
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        is_active=True,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        ) from None
    session.refresh(user)
    return user


def authenticate_user(session: Session, credentials: UserLogin) -> User:
    """Validate user credentials and return the user.

    Args:
        session: Database session for lookups.
        credentials: Login payload containing email and password.

    Returns:
        User: Authenticated user record.

    Raises:
        HTTPException: If credentials are invalid.
    """
    user = session.execute(
        select(User).where(User.email == credentials.email)
    ).scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return user


def issue_access_token(settings: Settings, user: User) -> str:
    """Issue a JWT access token for the given user.

    Args:
        settings: Application settings with JWT configuration.
        user: Authenticated user record.

    Returns:
        str: Encoded JWT access token.
    """
    return create_access_token(settings, subject=str(user.id), email=user.email)


def get_current_user(
    token: TokenDep,
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    """Resolve the authenticated user from the bearer token.

    Args:
        token: Bearer token extracted from the request.
        session: Database session for user lookup.
        settings: Application settings with JWT configuration.

    Returns:
        User: Authenticated user record.

    Raises:
        HTTPException: If the token is invalid or user is missing.
    """
    try:
        payload = decode_access_token(settings, token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        ) from None

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        )
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        ) from None
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        )
    return user
