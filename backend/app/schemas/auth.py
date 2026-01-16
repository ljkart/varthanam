"""Schemas for authentication and user identity responses."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Input payload for registering a new user."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    """Input payload for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserRead(BaseModel):
    """Safe user fields returned from authentication endpoints."""

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Bearer token response payload."""

    access_token: str
    token_type: str
