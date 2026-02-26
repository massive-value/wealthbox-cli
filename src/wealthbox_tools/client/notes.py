from __future__ import annotations

from typing import Any

from wealthbox_tools.models import NoteCreateInput, NoteListQuery, NoteUpdateInput


class NotesMixin:
    """Note resource methods. Mixed into WealthboxClient. (No delete — API does not support it.)"""

    async def list_notes(self, query: NoteListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/notes", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def get_note(self, note_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/notes/{note_id}")  # type: ignore[attr-defined]
        return resp.json()

    async def create_note(self, data: NoteCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/notes", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def update_note(self, note_id: int, data: NoteUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("PUT", f"/notes/{note_id}", json=payload)  # type: ignore[attr-defined]
        return resp.json()
