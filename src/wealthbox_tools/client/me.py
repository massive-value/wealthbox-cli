from __future__ import annotations

from typing import Any


class MeMixin:
    """Me Resource"""

    async def get_me(self) -> dict[str, Any]:
        resp = await self._request("GET", "/me")  # type: ignore[attr-defined]
        return resp.json()