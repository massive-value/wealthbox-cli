from __future__ import annotations

from typing import Any

from wealthbox_tools.models import ActivityListQuery


class ActivityMixin:
    """Activity Resource"""
    async def list_activity(self, query: ActivityListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/activity", params=params)  # type: ignore[attr-defined]
        return resp.json()