from __future__ import annotations

from .common import PaginationQuery

from .enums import ActivityTypeOptions


class ActivityListQuery(PaginationQuery):
    contact: int | None = None
    type: ActivityTypeOptions | None = None
    updated_since: str | None = None
    updated_before: str | None = None
    
