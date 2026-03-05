from __future__ import annotations

from typing import Any

from wealthbox_tools.models import CategoryListQuery, CategoryType


class CategoriesMixin:
    """Categories Resources"""

    async def list_categories(self, category: CategoryType, query: CategoryListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", f"/categories/{category}", params=params)  # type: ignore[attr-defined]
        return resp.json()