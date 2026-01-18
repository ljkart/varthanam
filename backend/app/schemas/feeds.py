"""Schemas for feed validation and creation endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FeedCreate(BaseModel):
    """Input payload for creating a feed."""

    url: str = Field(..., min_length=1)


class FeedRead(BaseModel):
    """Feed fields returned to API clients."""

    id: int
    url: str
    title: str
    site_url: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
