"""Schemas for article endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ArticleRead(BaseModel):
    """Article fields returned to API clients.

    Exposes safe, read-only fields for article listing.
    Does not include content field to keep responses lightweight.
    """

    id: int
    feed_id: int
    title: str
    url: str | None
    guid: str | None
    summary: str | None
    author: str | None
    published_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedArticlesResponse(BaseModel):
    """Paginated response wrapper for article listings.

    Includes pagination metadata alongside the items.
    """

    items: list[ArticleRead]
    total: int = Field(..., description="Total count of articles in this collection")
    limit: int = Field(..., description="Maximum items per page")
    offset: int = Field(..., description="Number of items skipped")
