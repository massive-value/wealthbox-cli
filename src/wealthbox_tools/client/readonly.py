from __future__ import annotations

from typing import Any

from wealthbox_tools.models import (
    ActivityListQuery,
    CategoryType,
)
from wealthbox_tools.models.common import PaginationQuery


class ReadOnlyMixin:
    """Read-only resource methods (me, users, activity, comments, custom_fields)."""

    async def get_me(self) -> dict[str, Any]:
        resp = await self._request("GET", "/me")  # type: ignore[attr-defined]
        return resp.json()
    
    async def list_users(self, query: PaginationQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/users", params=params)  # type: ignore[attr-defined]
        return resp.json()
    
    async def list_activity(self, query: ActivityListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/activity", params=params)  # type: ignore[attr-defined]
        return resp.json()
    
    async def list_custom_categories(self, category: CategoryType, *, document_type: str | None = None) -> dict[str, Any]:
        params = {"document_type": document_type} if document_type else None
        resp = await self._request("GET", f"/categories/{category}", params=params)  # type: ignore[attr-defined]
        return resp.json()