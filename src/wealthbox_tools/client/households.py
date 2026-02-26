from __future__ import annotations

from typing import Any

from wealthbox_tools.models import HouseholdMemberInput


class HouseholdsMixin:
    """Household membership methods."""

    async def add_household_member(
        self, household_id: int, data: HouseholdMemberInput
    ) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request(  # type: ignore[attr-defined]
            "POST", f"/households/{household_id}/members", json=payload
        )
        return resp.json()

    async def remove_household_member(
        self, household_id: int, member_id: int
    ) -> dict[str, Any]:
        resp = await self._request(  # type: ignore[attr-defined]
            "DELETE", f"/households/{household_id}/members/{member_id}"
        )
        # Wealthbox typically returns the household body, but normalize gracefully.
        try:
            return resp.json()
        except Exception:
            return {"ok": True, "household_id": household_id, "member_id": member_id}
