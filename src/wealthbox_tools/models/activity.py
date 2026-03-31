from __future__ import annotations

from .common import DateTimeField, WealthboxModel
from .enums import ActivityType


class ActivityListQuery(WealthboxModel):
    contact: int | None = None
    cursor: str | None = None
    type: ActivityType | None = None
    updated_since: DateTimeField = None
    updated_before: DateTimeField = None
    
