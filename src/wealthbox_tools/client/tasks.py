from __future__ import annotations

from typing import Any

from wealthbox_tools.models import TaskCreateInput, TaskListQuery, TaskUpdateInput


class TasksMixin:
    """Task resource methods. Mixed into WealthboxClient."""

    async def list_tasks(self, query: TaskListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/tasks", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def get_task(self, task_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/tasks/{task_id}")  # type: ignore[attr-defined]
        return resp.json()

    async def create_task(self, data: TaskCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/tasks", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def update_task(self, task_id: int, data: TaskUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("PUT", f"/tasks/{task_id}", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def delete_task(self, task_id: int) -> None:
        await self._request("DELETE", f"/tasks/{task_id}")  # type: ignore[attr-defined]
