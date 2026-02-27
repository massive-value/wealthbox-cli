from __future__ import annotations

from pydantic import Field

from .common import PaginationQuery, RequireAnyFieldModel, WealthboxModel, LinkedToRef
from .enums import EventsOrderOptions, EventsStateOptions, EmailInviteeTypeOptions


class EmailInvitees(WealthboxModel):
    id: int | None = None
    type: EmailInviteeTypeOptions | None = None


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
    starts_at: str | None = None
    ends_at: str | None = None
    repeats: bool | None = None
    event_category: int | None = None
    all_day: bool | None = None
    location: str | None = None
    description: str | None = None
    state: EventsStateOptions | None = None
    # visible_to: str | None = None
    email_invitees: bool | None = None
    linked_to: list[LinkedToRef] | None = None
    invitees: list[EmailInvitees] | None = None
    # custom_fields: str | None = None


class EventUpdateInput(RequireAnyFieldModel):
    title: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    repeats: bool | None = None
    event_category: int | None = None
    all_day: bool | None = None
    location: str | None = None
    description: str | None = None
    state: EventsStateOptions | None = None
    # visible_to: str | None = None
    email_invitees: bool | None = None
    linked_to: LinkedToRef | None = None
    invitees: list[EmailInvitees] | None = None
    # custom_fields: str | None = None
