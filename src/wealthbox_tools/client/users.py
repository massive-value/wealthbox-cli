from __future__ import annotations

from collections.abc import Callable
from typing import Any

from wealthbox_tools.models.common import PaginationQuery


class UsersMixin:
    """Users Resource"""

    async def list_users(self, query: PaginationQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/users", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def list_all_users(
        self,
        query: PaginationQuery | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Fetch every page of users. Use when full enumeration is required (e.g. firm bootstrap)."""
        params = query.model_dump(exclude_none=True) if query else {}
        params.pop("page", None)
        params.pop("per_page", None)
        return await self.fetch_all_pages(  # type: ignore[attr-defined]
            "/users", params, "users", on_progress=on_progress
        )