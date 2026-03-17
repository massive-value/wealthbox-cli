from __future__ import annotations

from typing import Any

from wealthbox_tools.models import (
    WorkflowCreateInput,
    WorkflowListQuery,
    WorkflowStepCompleteInput,
    WorkflowTemplateListQuery,
)


class WorkflowsMixin:
    """Workflows Resource"""

    async def list_workflows(self, query: WorkflowListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/workflows", params=params)  # type: ignore[attr-defined]
        return resp.json()

    async def get_workflow(self, workflow_id: int) -> dict[str, Any]:
        resp = await self._request("GET", f"/workflows/{workflow_id}")  # type: ignore[attr-defined]
        return resp.json()

    async def create_workflow(self, data: WorkflowCreateInput) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("POST", "/workflows", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def complete_workflow_step(
        self, workflow_id: int, step_id: int, data: WorkflowStepCompleteInput
    ) -> dict[str, Any]:
        payload = data.model_dump(exclude_none=True)
        resp = await self._request("PUT", f"/workflows/{workflow_id}/steps/{step_id}", json=payload)  # type: ignore[attr-defined]
        return resp.json()

    async def revert_workflow_step(self, workflow_id: int, step_id: int) -> dict[str, Any]:
        resp = await self._request("PUT", f"/workflows/{workflow_id}/steps/{step_id}", json={"revert": True})  # type: ignore[attr-defined]
        return resp.json()

    async def list_workflow_templates(self, query: WorkflowTemplateListQuery | None = None) -> dict[str, Any]:
        params = query.model_dump(exclude_none=True) if query else None
        resp = await self._request("GET", "/workflow_templates", params=params)  # type: ignore[attr-defined]
        return resp.json()
