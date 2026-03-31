from __future__ import annotations

from pydantic import Field

from .common import DateTimeField, LinkedToRef, PaginationQuery, RequireAnyFieldModel, WealthboxModel
from .custom_fields import CustomFieldValue
from .enums import OpportunityAmountKind, OpportunityOrder, OpportunityResourceType


class OpportunityAmount(WealthboxModel):
    amount: float
    currency: str = Field(min_length=1)
    kind: OpportunityAmountKind


class OpportunityListQuery(PaginationQuery):
    resource_id: int | None = Field(default=None, ge=1)
    resource_type: OpportunityResourceType | None = None
    order: OpportunityOrder | None = None
    include_closed: bool | None = None
    updated_since: DateTimeField = None
    updated_before: DateTimeField = None


class OpportunityCreateInput(WealthboxModel):
    name: str = Field(min_length=1)
    description: str | None = None
    target_close: str = Field(min_length=1)
    probability: int = Field(ge=0, le=100)
    stage: int = Field(ge=1)
    manager: int | None = None
    amounts: list[OpportunityAmount] | None = None
    linked_to: list[LinkedToRef] | None = None
    visible_to: str | None = None
    custom_fields: list[CustomFieldValue] | None = None


class OpportunityUpdateInput(RequireAnyFieldModel):
    name: str | None = None
    description: str | None = None
    target_close: str | None = None
    probability: int | None = Field(default=None, ge=0, le=100)
    stage: int | None = Field(default=None, ge=1)
    manager: int | None = None
    amounts: list[OpportunityAmount] | None = None
    linked_to: list[LinkedToRef] | None = None
    visible_to: str | None = None
    custom_fields: list[CustomFieldValue] | None = None
