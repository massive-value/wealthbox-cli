"""Pydantic models for metadata tool validation."""
from __future__ import annotations

from typing import Any

from .common import PaginationQuery, WealthboxModel
from .enums import DocumentType


class CustomFieldValue(WealthboxModel):
    id: int | None = None
    name: str | None = None
    value: Any | None = None


class CategoryListQuery(PaginationQuery):
    document_type: DocumentType | None = None
