from __future__ import annotations

from .common import WealthboxModel

from .enums import ActivityType


class ActivityListQuery(WealthboxModel):
    contact: int | None = None
    cursor: str | None = None
    type: ActivityType | None = None
    updated_since: str | None = None
    updated_before: str | None = None
    
