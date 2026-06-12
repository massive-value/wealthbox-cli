from __future__ import annotations

from typing import Any

from wealthbox_tools.models import CommentListQuery

from .base import _RequestMixinBase


class CommentsMixin(_RequestMixinBase):
    """Comments Resource"""

    async def list_comments(self, query: CommentListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/comments", params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def get_comments_for_resource(
        self, resource_type: str, resource_id: int
    ) -> list[dict[str, Any]]:
        """Fetch all comments for a specific resource."""
        params: dict[str, Any] = {"resource_type": resource_type, "resource_id": resource_id}
        resp = await self._request("GET", "/comments", params=params)
        comments: list[dict[str, Any]] = resp.json().get("comments", [])
        return comments
