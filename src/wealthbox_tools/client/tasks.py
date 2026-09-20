from __future__ import annotations

from typing import Any

from wealthbox_tools.models import TaskCreateInput, TaskListQuery, TaskUpdateInput

from .base import _RequestMixinBase, merge_records_by_id


class TasksMixin(_RequestMixinBase):
    """Task resource methods. Mixed into WealthboxClient."""

    async def list_tasks(self, query: TaskListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/tasks", params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def list_tasks_all_statuses(self, query: TaskListQuery | None = None) -> dict[str, Any]:
        """List tasks across both completion states.

        ``GET /tasks`` treats ``completed`` as a two-way switch, not an
        "include": omitted or ``false`` returns open tasks only, ``true``
        returns completed only. There is no value that returns both, so this
        issues the two calls **sequentially** (the token allows 300 requests
        per 5 minutes; fanning out competes with any other walk in flight)
        and merges the results by ``id``.

        Any ``completed`` value on ``query`` is ignored. Pagination flags are
        honoured per call, so ``--page 2`` means page 2 of each state.
        """
        batches = []
        for completed in (False, True):
            params = query.model_dump(exclude_none=True) if query else {}
            params["completed"] = completed
            resp = await self._request("GET", "/tasks", params=params)
            batches.append(resp.json().get("tasks", []))
        tasks = merge_records_by_id(batches)
        return {"tasks": tasks, "meta": {"total_count": len(tasks)}}

    async def get_task(self, task_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/tasks/{task_id}")
        data: dict[str, Any] = resp.json()
        return data

    async def create_task(self, data: TaskCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/tasks", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def update_task(self, task_id: int, data: TaskUpdateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_unset=True)
        resp = await self._request("PUT", f"/tasks/{task_id}", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def delete_task(self, task_id: int) -> None:
        await self._request("DELETE", f"/tasks/{task_id}")
