from __future__ import annotations

from pydantic import Field, model_validator

from .common import PaginationQuery, RequireAnyFieldModel, WealthboxModel, LinkedToRef

from .enums import TaskFrameOptions, TaskResourseTypeOptions, TaskTypeOptions, TaskPriorityOptions



class TaskListQuery(PaginationQuery):
    resource_id: int | None = None
    resource_type: TaskResourseTypeOptions | None = None
    assigned_to: int | None = None
    assigned_to_team: int | None = None
    created_by: int | None = None
    completed: bool | None = None
    task_type: TaskTypeOptions | None = None
    updated_since: str | None = None
    updated_before: str | None = None


class TaskCreateInput(WealthboxModel):
    name: str = Field(min_length=1)
    due_date: str | None = None
    frame: TaskFrameOptions | None = None
    complete: bool | None = None
    category: int | None = None
    linked_to: list[LinkedToRef] | None = None
    priority: TaskPriorityOptions | None = None
    # visible_to: str | None = None
    # due_later: str | None = None
    # subtasks: SubTaskInput | None = None
    # custom_fields: TaskCustomFieldInput | None = None
    assigned_to: int | None = None
    assigned_to_team: int | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_assignment_target(self) -> "TaskCreateInput":
        if self.assigned_to is not None and self.assigned_to_team is not None:
            raise ValueError("Provide only one of assigned_to or assigned_to_team_id.")
        return self



class TaskUpdateInput(RequireAnyFieldModel):
    name: str | None = Field(default=None, min_length=1)
    due_date: str | None = None
    frame: TaskFrameOptions | None = None
    complete: bool | None = None
    category: int | None = None
    linked_to: list[LinkedToRef] | None = None
    priority: TaskPriorityOptions | None = None
    # visible_to: str | None = None
    # due_later: str | None = None
    # subtasks: SubTaskInput | None = None
    # custom_fields: TaskCustomFieldInput | None = None
    assigned_to: int | None = None
    assigned_to_team: int | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_assignment_target(self) -> "TaskUpdateInput":
        if self.assigned_to is not None and self.assigned_to_team is not None:
            raise ValueError("Provide only one of assigned_to_user_id or assigned_to_team_id.")
        return self
