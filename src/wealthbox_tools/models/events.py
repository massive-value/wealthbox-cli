from __future__ import annotations

from pydantic import Field

from .common import PaginationQuery, RequireAnyFieldModel, WealthboxModel
from .enums import EventsOrderOptions


class EventListQuery(PaginationQuery):
    resource_id: int | None = None
    resource_type: str | None = None
    start_date_min: str | None = None
    start_date_max: str | None = None
    order: EventsOrderOptions | None = None
    updated_since: str | None = None
    updated_before: str | None = None


class EventCreateInput(WealthboxModel):
    title: str = Field(min_length=1)
    description: str | None = None
    starts_at: str = Field(min_length=1)
    ends_at: str | None = None
    location: str | None = None
    category_id: int | None = None


class EventUpdateInput(RequireAnyFieldModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    starts_at: str | None = Field(default=None, min_length=1)
    ends_at: str | None = None
    location: str | None = None
    category_id: int | None = None
