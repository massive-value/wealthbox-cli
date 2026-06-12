from __future__ import annotations

from typing import Any

from wealthbox_tools.models import HouseholdMemberInput

from .base import _RequestMixinBase


class HouseholdsMixin(_RequestMixinBase):
    """Household membership methods."""

    async def add_household_member(
        self, household_id: int, data: HouseholdMemberInput
    ) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request(
            "POST", f"/households/{household_id}/members", json=payload
        )
        body: dict[str, Any] = resp.json()
        return body

    async def remove_household_member(
        self, household_id: int, member_id: int
    ) -> dict[str, Any]:
        resp = await self._request(
            "DELETE", f"/households/{household_id}/members/{member_id}"
        )
        # Wealthbox typically returns the household body, but may return empty body.
        try:
            body: dict[str, Any] = resp.json()
            return body
        except ValueError:
            return {"ok": True, "household_id": household_id, "member_id": member_id}
