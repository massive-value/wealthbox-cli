from __future__ import annotations

from .common import PaginationQuery


class ActivityListQuery(PaginationQuery):
    contact: int | None = None
    cursor: str | None = None
    type: str | None = None
    updated_since: str | None = None
    updated_before: str | None = None
    
