"""Pydantic models for metadata tool validation."""
from __future__ import annotations

from pydantic import BaseModel

from .enums import DocumentTypeOptions


class CustomFieldsListQuery(BaseModel):
    document_type: DocumentTypeOptions | None = None
