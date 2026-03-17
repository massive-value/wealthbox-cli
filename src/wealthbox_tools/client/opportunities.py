from __future__ import annotations

from typing import Any

from wealthbox_tools.models import OpportunityCreateInput, OpportunityListQuery, OpportunityUpdateInput


class OpportunitiesMixin:
    """Opportunities Resource"""

    async def list_opportunities(self, query: OpportunityListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/opportunities", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def get_opportunity(self, opportunity_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/opportunities/{opportunity_id}")  # type: ignore[attr-defined]
        return resp.json()

    async def create_opportunity(self, data: OpportunityCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/opportunities", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def update_opportunity(self, opportunity_id: int, data: OpportunityUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_unset=True)
        resp = await self._request("PUT", f"/opportunities/{opportunity_id}", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def delete_opportunity(self, opportunity_id: int) -> None:
        await self._request("DELETE", f"/opportunities/{opportunity_id}")  # type: ignore[attr-defined]
