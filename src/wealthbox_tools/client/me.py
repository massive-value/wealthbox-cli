from __future__ import annotations

from typing import Any

from .base import _RequestMixinBase


class MeMixin(_RequestMixinBase):
    """Me Resource"""

    async def get_me(self) -> dict[str, Any]:
        resp = await self._request("GET", "/me")
        data: dict[str, Any] = resp.json()
        return data
