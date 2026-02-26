from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wealthbox_tools.models import ContactCreateInput, ContactListQuery, ContactUpdateInput

if TYPE_CHECKING:
    pass


class ContactsMixin:
    """Contact resource methods. Mixed into WealthboxClient."""

    async def list_contacts(self, query: ContactListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/contacts", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def get_contact(self, contact_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/contacts/{contact_id}")  # type: ignore[attr-defined]
        return resp.json()

    async def create_contact(self, data: ContactCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/contacts", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def update_contact(self, contact_id: int, data: ContactUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("PUT", f"/contacts/{contact_id}", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def delete_contact(self, contact_id: int) -> None:
        await self._request("DELETE", f"/contacts/{contact_id}")  # type: ignore[attr-defined]
