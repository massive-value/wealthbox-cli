from __future__ import annotations

from typing import Any

from wealthbox_tools.models import ProjectCreateInput, ProjectListQuery, ProjectUpdateInput


class ProjectsMixin:
    """Projects Resource"""

    async def list_projects(self, query: ProjectListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/projects", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def get_project(self, project_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/projects/{project_id}")  # type: ignore[attr-defined]
        return resp.json()

    async def create_project(self, data: ProjectCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/projects", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def update_project(self, project_id: int, data: ProjectUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_unset=True)
        resp = await self._request("PUT", f"/projects/{project_id}", json=payload)  # type: ignore[attr-defined]
        return resp.json()
