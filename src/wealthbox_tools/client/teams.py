from __future__ import annotations

from .base import PaginatedResponse, _RequestMixinBase


class TeamsMixin(_RequestMixinBase):
    """Teams and user groups. Both are read-only lookup resources.

    Workspaces hold a handful of each, so a single page always suffices in
    practice — but both endpoints return standard pagination ``meta``, so we
    go through ``fetch_all_pages`` anyway and stay correct for a large firm.
    """

    async def list_teams(self) -> PaginatedResponse:
        """List every team in the workspace (id, name, members)."""
        return await self.fetch_all_pages("/teams", {}, "teams")

    async def list_user_groups(self) -> PaginatedResponse:
        """List every user group in the workspace (id, name, user, members)."""
        return await self.fetch_all_pages("/user_groups", {}, "user_groups")


__all__ = ["TeamsMixin"]

