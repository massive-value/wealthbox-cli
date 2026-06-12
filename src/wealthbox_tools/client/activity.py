from __future__ import annotations

from typing import Any

from wealthbox_tools.models import ActivityListQuery

from .base import _RequestMixinBase


class ActivityMixin(_RequestMixinBase):
    """Activity Resource"""
    async def list_activity(self, query: ActivityListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/activity", params=params)
        data: dict[str, Any] = resp.json()
        return data
