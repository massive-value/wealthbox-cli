from __future__ import annotations

from collections.abc import Callable
from typing import Any

from wealthbox_tools.models import CategoryListQuery, CategoryType

from .base import PaginatedResponse, _RequestMixinBase


class CategoriesMixin(_RequestMixinBase):
    """Categories Resources"""

    async def list_categories(self, category: CategoryType, query: CategoryListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", f"/categories/{category}", params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def list_all_categories(
        self,
        category: CategoryType,
        query: CategoryListQuery | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> PaginatedResponse:
        """Fetch every page of a category type. Custom fields use collection key 'custom_fields'."""
        params = query.model_dump(exclude_none=True) if query else {}
        params.pop("page", None)
        params.pop("per_page", None)
        collection_key = "custom_fields" if category is CategoryType.CUSTOM_FIELDS else category.value
        return await self.fetch_all_pages(
            f"/categories/{category}", params, collection_key, on_progress=on_progress
        )
