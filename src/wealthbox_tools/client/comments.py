from __future__ import annotations

from typing import Any

from wealthbox_tools.models import CommentListQuery


class CommentsMixin:
    """Comments Resource"""

    async def list_comments(self, query: CommentListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/comments", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def get_comments_for_resource(
        self, resource_type: str, resource_id: int
    ) -> list[dict[str, Any]]:
        """Fetch all comments for a specific resource."""
        params = {"resource_type": resource_type, "resource_id": resource_id}
        resp = await self._request("GET", "/comments", params=params)  # type: ignore[attr-defined]
        return resp.json().get("comments", [])
