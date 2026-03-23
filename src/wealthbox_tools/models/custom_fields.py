"""Pydantic models for metadata tool validation."""
from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import PaginationQuery, WealthboxModel
from .enums import DocumentType


class CustomFieldValue(WealthboxModel):
    id: int | None = Field(default=None, ge=1)
    name: str | None = None
    value: Any | None = None


class CategoryListQuery(PaginationQuery):
    document_type: DocumentType | None = None
