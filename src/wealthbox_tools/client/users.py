from __future__ import annotations

from typing import Any

from wealthbox_tools.models.common import PaginationQuery


class UsersMixin:
    """Users Resource"""
    
    async def list_users(self, query: PaginationQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/users", params=params)  # type: ignore[attr-defined]
        return resp.json()