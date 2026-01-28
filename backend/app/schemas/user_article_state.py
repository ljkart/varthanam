"""Schemas for user article state endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserArticleStateRead(BaseModel):
    """Response model for user article state.

    Returns the current read/saved state for a specific article
    from the authenticated user's perspective.
    """

    article_id: int
    is_read: bool
    is_saved: bool
    read_at: datetime | None
    saved_at: datetime | None

    model_config = {"from_attributes": True}
