from __future__ import annotations

from typing import Any

from wealthbox_tools.models import CommentListQuery


class CommentsMixin:
    """Comments Resource"""

    async def list_comments(self, query: CommentListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/comments", params=params)  # type: ignore[attr-defined]
        return resp.json()
