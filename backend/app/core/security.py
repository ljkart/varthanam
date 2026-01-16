"""Security utilities for password hashing and verification."""

from passlib.context import CryptContext

_PWD_CONTEXT = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


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
