from __future__ import annotations

from pydantic import Field

from .common import DateField, DateTimeField, NonNullDateTimeField, PaginationQuery, RequireAnyFieldModel, WealthboxModel, LinkedToRef
from .enums import EventsOrder, EventsState, EmailInviteeType, TaskResourceType


class EmailInvitees(WealthboxModel):
    id: int | None = Field(default=None, ge=1)
    type: EmailInviteeType | None = None


class EventListQuery(PaginationQuery):
    resource_id: int | None = Field(default=None, ge=1)
    resource_type: TaskResourceType | None = None
    start_date_min: DateField = None
    start_date_max: DateField = None
    order: EventsOrder | None = None
    updated_since: DateTimeField = None
    updated_before: DateTimeField = None


class EventCreateInput(WealthboxModel):
    title: str = Field(min_length=1)
    starts_at: NonNullDateTimeField = Field(min_length=1)
    ends_at: NonNullDateTimeField = Field(min_length=1)
    repeats: bool | None = None
    event_category: int | None = Field(default=None, ge=1)
    all_day: bool | None = None
    location: str | None = None
    description: str | None = None
    state: EventsState | None = None
    # visible_to: str | None = None
    email_invitees: bool | None = None
    linked_to: list[LinkedToRef] | None = None
    invitees: list[EmailInvitees] | None = None
    # custom_fields: str | None = None


class EventUpdateInput(RequireAnyFieldModel):
    title: str | None = None
    starts_at: DateTimeField = None
    ends_at: DateTimeField = None
    repeats: bool | None = None
    event_category: int | None = Field(default=None, ge=1)
    all_day: bool | None = None
    location: str | None = None
    description: str | None = None
    state: EventsState | None = None
    # visible_to: str | None = None
    email_invitees: bool | None = None
    linked_to: list[LinkedToRef] | None = None
    invitees: list[EmailInvitees] | None = None
    # custom_fields: str | None = None
