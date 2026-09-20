from __future__ import annotations

from typing import Any

from wealthbox_tools.models import (
    WorkflowCreateInput,
    WorkflowListQuery,
    WorkflowStatus,
    WorkflowStepCompleteInput,
    WorkflowTemplateListQuery,
)

from .base import _RequestMixinBase, merge_records_by_id


class WorkflowsMixin(_RequestMixinBase):
    """Workflows Resource"""

    async def list_workflows(self, query: WorkflowListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/workflows", params=params)
        data: dict[str, Any] = resp.json()
        return data

    async def list_workflows_all_statuses(self, query: WorkflowListQuery | None = None) -> dict[str, Any]:
        """List workflows across every status.

        ``GET /workflows`` defaults to ``active`` when no ``status`` is given
        and accepts only one status at a time, so this issues one call per
        status **sequentially** (see the rate-limit note on
        ``TasksMixin.list_tasks_all_statuses``) and merges by ``id``.

        Any ``status`` on ``query`` is ignored. Pagination flags are honoured
        per call, so ``--page 2`` means page 2 of each status.
        """
        batches = []
        for status in WorkflowStatus:
            params = query.model_dump(exclude_none=True) if query else {}
            params["status"] = status.value
            resp = await self._request("GET", "/workflows", params=params)
            batches.append(resp.json().get("workflows", []))
        workflows = merge_records_by_id(batches)
        return {"workflows": workflows, "meta": {"total_count": len(workflows)}}

    async def get_workflow(self, workflow_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/workflows/{workflow_id}")
        data: dict[str, Any] = resp.json()
        return data

    async def create_workflow(self, data: WorkflowCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/workflows", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def complete_workflow_step(
        self, workflow_id: int, step_id: int, data: WorkflowStepCompleteInput
    ) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("PUT", f"/workflows/{workflow_id}/steps/{step_id}", json=payload)
        body: dict[str, Any] = resp.json()
        return body

    async def revert_workflow_step(self, workflow_id: int, step_id: int) -> dict[str, Any]:
        resp = await self._request("PUT", f"/workflows/{workflow_id}/steps/{step_id}", json={"revert": True})
        body: dict[str, Any] = resp.json()
        return body

    async def list_workflow_templates(self, query: WorkflowTemplateListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/workflow_templates", params=params)
        data: dict[str, Any] = resp.json()
        return data
