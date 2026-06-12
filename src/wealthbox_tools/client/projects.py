from __future__ import annotations

from typing import Any

from wealthbox_tools.models import ProjectCreateInput, ProjectListQuery, ProjectUpdateInput

from .base import _RequestMixinBase


class ProjectsMixin(_RequestMixinBase):
    """Projects Resource"""

    async def list_projects(self, query: ProjectListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/projects", params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def get_project(self, project_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/projects/{project_id}")
        data: dict[str, Any] = resp.json()
        return data

    async def create_project(self, data: ProjectCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/projects", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def update_project(self, project_id: int, data: ProjectUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_unset=True)
        resp = await self._request("PUT", f"/projects/{project_id}", json=payload)
        body: dict[str, Any] = resp.json()
        return body
