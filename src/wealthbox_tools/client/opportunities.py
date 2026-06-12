from __future__ import annotations

from typing import Any

from wealthbox_tools.models import OpportunityCreateInput, OpportunityListQuery, OpportunityUpdateInput

from .base import _RequestMixinBase


class OpportunitiesMixin(_RequestMixinBase):
    """Opportunities Resource"""

    async def list_opportunities(self, query: OpportunityListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/opportunities", params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def get_opportunity(self, opportunity_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/opportunities/{opportunity_id}")
        data: dict[str, Any] = resp.json()
        return data

    async def create_opportunity(self, data: OpportunityCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/opportunities", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def update_opportunity(self, opportunity_id: int, data: OpportunityUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_unset=True)
        resp = await self._request("PUT", f"/opportunities/{opportunity_id}", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def delete_opportunity(self, opportunity_id: int) -> None:
        await self._request("DELETE", f"/opportunities/{opportunity_id}")
