from __future__ import annotations

from pydantic import Field

from .common import DateTimeField, LinkedToRef, PaginationQuery, WealthboxModel
from .enums import WorkflowResourceType, WorkflowStatus


class WorkflowMilestone(WealthboxModel):
    id: int = Field(ge=1)
    name: str = Field(min_length=1)
    milestone_date: str = Field(min_length=1)


class WorkflowListQuery(PaginationQuery):
    resource_id: int | None = Field(default=None, ge=1)
    resource_type: WorkflowResourceType | None = None
    status: WorkflowStatus | None = None
    updated_since: DateTimeField = None
    updated_before: DateTimeField = None


class WorkflowCreateInput(WealthboxModel):
    label: str | None = None
    linked_to: list[LinkedToRef] | None = None
    visible_to: str | None = None
    workflow_template: int = Field(ge=1)
    starts_at: str | None = None
    workflow_milestones: list[WorkflowMilestone] | None = None


class WorkflowTemplateListQuery(PaginationQuery):
    resource_id: int | None = Field(default=None, ge=1)
    resource_type: WorkflowResourceType | None = None
    status: WorkflowStatus | None = None
    updated_since: DateTimeField = None
    updated_before: DateTimeField = None


class WorkflowStepCompleteInput(WealthboxModel):
    complete: bool = Field(default=True)
    workflow_outcome_id: int | None = None
    # When selecting an outcome with the “Restart Step” action, this indicates
    # whether the restarted step will have a due date.
    due_date_set: bool = Field(default=False)
    due_date: str | None = None


class WorkflowStepRevertInput(WealthboxModel):
    revert: bool = Field(default=True)