from __future__ import annotations

from typing import Any

from wealthbox_tools.models import CategoryType


class CategoriesMixin:
    """Categories Resources"""

    async def list_categories(self, category: CategoryType, *, document_type: str | None = None) -> dict[str, Any]:
        params = {"document_type": document_type} if document_type else None
        resp = await self._request("GET", f"/categories/{category}", params=params)  # type: ignore[attr-defined]
        return resp.json()