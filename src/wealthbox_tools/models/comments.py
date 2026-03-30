from __future__ import annotations

from pydantic import Field

from .common import DateTimeField, PaginationQuery
from .enums import CommentResourceType


class CommentListQuery(PaginationQuery):
    resource_id: int | None = Field(default=None, ge=1)
    resource_type: CommentResourceType | None = None
    updated_since: DateTimeField = None
    updated_before: DateTimeField = None