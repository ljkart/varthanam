"""Security utilities for password hashing and JWT handling."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.settings import Settings

_PWD_CONTEXT = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
_JWT_ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """Hash a plaintext password for storage.

    Args:
        password: Plaintext password to hash.

    Returns:
        str: A salted password hash.
    """
    return _PWD_CONTEXT.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Args:
        plain_password: Plaintext password to verify.
        hashed_password: Stored hash to compare against.

    Returns:
        bool: True if the password matches the hash.
    """
    return _PWD_CONTEXT.verify(plain_password, hashed_password)


def create_access_token(settings: Settings, *, subject: str, email: str) -> str:
    """Create a signed JWT access token with subject, email, and expiry claims.

    Args:
        settings: Application settings containing JWT configuration.
        subject: Subject identifier for the token (usually the user ID).
        email: Email address claim for auditing.

    Returns:
        str: Encoded JWT access token.
    """
    now = datetime.now(tz=UTC)
    expires_at = now + timedelta(minutes=settings.jwt_access_token_exp_minutes)
    payload = {"sub": subject, "email": email, "iat": now, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=_JWT_ALGORITHM)


def decode_access_token(settings: Settings, token: str) -> dict[str, object]:
    """Decode and validate a JWT access token.

    Args:
        settings: Application settings containing JWT configuration.
        token: Encoded JWT access token.

    Returns:
        dict[str, object]: Decoded token payload.

    Raises:
        jwt.PyJWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=[_JWT_ALGORITHM])
