from __future__ import annotations

from typing import Any

from wealthbox_tools.models import EventCreateInput, EventListQuery, EventUpdateInput


class EventsMixin:
    """Event resource methods. Mixed into WealthboxClient."""

    async def list_events(self, query: EventListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/events", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def get_event(self, event_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/events/{event_id}")  # type: ignore[attr-defined]
        return resp.json()

    async def create_event(self, data: EventCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/events", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def update_event(self, event_id: int, data: EventUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("PUT", f"/events/{event_id}", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def delete_event(self, event_id: int) -> None:
        await self._request("DELETE", f"/events/{event_id}")  # type: ignore[attr-defined]
