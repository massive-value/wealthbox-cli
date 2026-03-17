from __future__ import annotations

from .common import PaginationQuery


class CommentListQuery(PaginationQuery):
    resource_id: int | None = None
    resource_type: str | None = None
    updated_since: str | None = None
    updated_before: str | None = None