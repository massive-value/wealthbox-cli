from __future__ import annotations

from typing import Any

from wealthbox_tools.models import (
    ActivityListQuery,
    CustomFieldsListQuery,
)


class ReadOnlyMixin:
    """Read-only resource methods (me, users, activity, comments, custom_fields)."""

    async def get_me(self) -> dict[str, Any]:
        resp = await self._request("GET", "/me")  # type: ignore[attr-defined]
        return resp.json()
    
    async def list_users(self, page: int | None = None, per_page: int | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        resp = await self._request("GET", "/users", params=params or None)  # type: ignore[attr-defined]
        return resp.json()
    
    async def list_activity(self, query: ActivityListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/activity", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def list_custom_fields(self, query: CustomFieldsListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/categories/custom_fields", params=params)  # type: ignore[attr-defined]
        return resp.json()
