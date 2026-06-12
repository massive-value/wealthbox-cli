from __future__ import annotations

from collections.abc import Callable
from typing import Any

from wealthbox_tools.models.common import PaginationQuery

from .base import PaginatedResponse, _RequestMixinBase


class UsersMixin(_RequestMixinBase):
    """Users Resource"""

    async def list_users(self, query: PaginationQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/users", params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def list_all_users(
        self,
        query: PaginationQuery | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> PaginatedResponse:
        """Fetch every page of users. Use when full enumeration is required (e.g. firm bootstrap)."""
        params = query.model_dump(exclude_none=True) if query else {}
        params.pop("page", None)
        params.pop("per_page", None)
        return await self.fetch_all_pages(
            "/users", params, "users", on_progress=on_progress
        )
