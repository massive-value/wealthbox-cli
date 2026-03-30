from __future__ import annotations

from pydantic import Field

from .common import DateTimeField, PaginationQuery, RequireAnyFieldModel, WealthboxModel
from .custom_fields import CustomFieldValue


class ProjectListQuery(PaginationQuery):
    updated_since: DateTimeField = None
    updated_before: DateTimeField = None


class ProjectCreateInput(WealthboxModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    organizer: int | None = None
    visible_to: str | None = None
    custom_fields: list[CustomFieldValue] | None = None


class ProjectUpdateInput(RequireAnyFieldModel):
    name: str | None = None
    description: str | None = None
    organizer: int | None = None
    visible_to: str | None = None
    custom_fields: list[CustomFieldValue] | None = None
