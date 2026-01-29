"""Schemas for Rule CRUD endpoints.

Defines request/response models for creating, updating, and reading rules.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RuleCreate(BaseModel):
    """Input payload for creating a rule.

    Required fields:
    - name: Human-readable identifier for the rule
    - frequency_minutes: How often the rule should be executed

    Optional fields:
    - include_keywords: Comma-separated keywords to match (article must contain)
    - exclude_keywords: Comma-separated keywords to exclude (article must not contain)
    - collection_id: Scope rule to a specific collection (null = all collections)
    - is_active: Whether the rule should be executed (default: true)

    Keyword validation:
    - Keywords must be non-empty strings if provided (min_length=1)
    """

    name: str = Field(..., min_length=1)
    frequency_minutes: int = Field(..., gt=0)
    include_keywords: str | None = Field(default=None, min_length=1)
    exclude_keywords: str | None = Field(default=None, min_length=1)
    collection_id: int | None = None
    is_active: bool = True


class RuleUpdate(BaseModel):
    """Input payload for updating a rule.

    All fields are optional - only provided fields will be updated.
    """

    name: str | None = Field(default=None, min_length=1)
    frequency_minutes: int | None = Field(default=None, gt=0)
    include_keywords: str | None = Field(default=None, min_length=1)
    exclude_keywords: str | None = Field(default=None, min_length=1)
    collection_id: int | None = None
    is_active: bool | None = None


class RuleRead(BaseModel):
    """Rule fields returned to API clients.

    Includes all rule configuration and scheduling metadata.
    Note: last_run_at is included but will be null until rule execution
    is implemented.
    """

    id: int
    name: str
    include_keywords: str | None
    exclude_keywords: str | None
    collection_id: int | None
    frequency_minutes: int
    last_run_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
