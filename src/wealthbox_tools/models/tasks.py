from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .common import PaginationQuery, RequireAnyFieldModel, WealthboxModel

from .enums import TaskFrameOptions



class TaskListQuery(PaginationQuery):
    title: str | None = None
    assigned_to_user_id: int | None = None
    assigned_to_team_id: int | None = None
    category_id: int | None = None
    completed: bool | None = None
    due_date: str | None = None
    updated_since: str | None = None
    updated_before: str | None = None


class TaskCreateInput(WealthboxModel):
    title: str = Field(min_length=1)
    due_date: str = Field(min_length=1)
    frame: TaskFrameOptions | None = None
    description: str | None = None
    assigned_to_user_id: int | None = None
    assigned_to_team_id: int | None = None
    category_id: int | None = None

    @model_validator(mode="after")
    def validate_assignment_target(self) -> "TaskCreateInput":
        if self.assigned_to_user_id is not None and self.assigned_to_team_id is not None:
            raise ValueError("Provide only one of assigned_to_user_id or assigned_to_team_id.")
        return self


class TaskUpdateInput(RequireAnyFieldModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    due_date: str | None = None
    frame: Literal["today", "tomorrow", "this_week", "next_week", "future", "specific"] | None = None
    assigned_to_user_id: int | None = None
    assigned_to_team_id: int | None = None
    category_id: int | None = None
    completed: bool | None = None

    @model_validator(mode="after")
    def validate_assignment_target(self) -> "TaskUpdateInput":
        if self.assigned_to_user_id is not None and self.assigned_to_team_id is not None:
            raise ValueError("Provide only one of assigned_to_user_id or assigned_to_team_id.")
        return self
