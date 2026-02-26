"""Pydantic models for metadata tool validation."""
from __future__ import annotations

from pydantic import BaseModel
from typing import Any

from .common import WealthboxModel
from .enums import DocumentTypeOptions


class CustomFieldValue(WealthboxModel):
    id: int | None = None
    name: str | None = None
    value: Any | None = None


class CustomFieldsListQuery(BaseModel):
    document_type: DocumentTypeOptions | None = None
