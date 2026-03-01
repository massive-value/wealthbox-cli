from __future__ import annotations

from pydantic import Field, model_validator

from .common import PaginationQuery, RequireAnyFieldModel, WealthboxModel, LinkedToRef

from .enums import TaskType, TaskPriority, TaskFrame, TaskResourceType


def _validate_assignment_target(assigned_to: int | None, assigned_to_team: int | None) -> None:
    if assigned_to is not None and assigned_to_team is not None:
        raise ValueError("Provide only one of assigned_to or assigned_to_team.")



class TaskListQuery(PaginationQuery):
    resource_id: int | None = None
    resource_type: TaskResourceType | None = None
    assigned_to: int | None = None
    assigned_to_team: int | None = None
    created_by: int | None = None
    completed: bool | None = None
    task_type: TaskType | None = None
    updated_since: str | None = None
    updated_before: str | None = None


class TaskCreateInput(WealthboxModel):
    name: str = Field(min_length=1)
    due_date: str | None = None
    frame: TaskFrame | None = None
    complete: bool | None = None
    category: int | None = None
    linked_to: list[LinkedToRef] | None = None
    priority: TaskPriority | None = None
    # visible_to: str | None = None
    # due_later: str | None = None
    # subtasks: SubTaskInput | None = None
    # custom_fields: TaskCustomFieldInput | None = None
    assigned_to: int | None = None
    assigned_to_team: int | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_assignment_target(self) -> "TaskCreateInput":
        _validate_assignment_target(self.assigned_to, self.assigned_to_team)
        return self

    @model_validator(mode="after")
    def validate_due_date_xor_frame(self) -> "TaskCreateInput":
        if (self.due_date is None) == (self.frame is None):
            # both None OR both set
            raise ValueError("Provide exactly one of due_date or frame (not both).")
        return self



class TaskUpdateInput(RequireAnyFieldModel):
    name: str | None = Field(default=None, min_length=1)
    due_date: str | None = None
    frame: TaskFrame | None = None
    complete: bool | None = None
    category: int | None = None
    linked_to: list[LinkedToRef] | None = None
    priority: TaskPriority | None = None
    # visible_to: str | None = None
    # due_later: str | None = None
    # subtasks: SubTaskInput | None = None
    # custom_fields: TaskCustomFieldInput | None = None
    assigned_to: int | None = None
    assigned_to_team: int | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_assignment_target(self) -> "TaskUpdateInput":
        _validate_assignment_target(self.assigned_to, self.assigned_to_team)
        return self
