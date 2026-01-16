"""Pytest configuration for backend tests."""

from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
