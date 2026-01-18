"""Schemas for collection CRUD endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CollectionCreate(BaseModel):
    """Input payload for creating a collection."""

    name: str = Field(..., min_length=1)
    description: str | None = None


class CollectionUpdate(BaseModel):
    """Input payload for updating a collection."""

    name: str | None = Field(default=None, min_length=1)
    description: str | None = None


class CollectionRead(BaseModel):
    """Collection fields returned to API clients."""

    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CollectionFeedCreate(BaseModel):
    """Input payload for assigning a feed to a collection."""

    feed_id: int = Field(..., ge=1)


class CollectionFeedRead(BaseModel):
    """Relationship fields returned for collection feed assignments."""

    collection_id: int
    feed_id: int

    model_config = {"from_attributes": True}
