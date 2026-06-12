from __future__ import annotations

from collections.abc import Callable
from typing import Any

from wealthbox_tools.models import ContactCreateInput, ContactListQuery, ContactUpdateInput

from .base import PaginatedResponse, _RequestMixinBase


class ContactsMixin(_RequestMixinBase):
    """Contact resource methods. Mixed into WealthboxClient."""

    async def list_contacts(self, query: ContactListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/contacts", params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def get_contact(self, contact_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/contacts/{contact_id}")
        data: dict[str, Any] = resp.json()
        return data

    async def create_contact(self, data: ContactCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/contacts", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def update_contact(self, contact_id: int, data: ContactUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_unset=True)
        resp = await self._request("PUT", f"/contacts/{contact_id}", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def delete_contact(self, contact_id: int) -> None:
        await self._request("DELETE", f"/contacts/{contact_id}")

    async def list_all_contacts(
        self,
        query: ContactListQuery | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> PaginatedResponse:
        """Fetch all pages of contacts. Use when client-side filtering requires the full dataset."""
        params = query.model_dump(exclude_none=True) if query else {}
        # Remove pagination fields — fetch_all_pages controls these
        params.pop("page", None)
        params.pop("per_page", None)
        return await self.fetch_all_pages("/contacts", params, "contacts", on_progress=on_progress)
