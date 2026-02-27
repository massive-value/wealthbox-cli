from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator



class WealthboxModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class RequireAnyFieldModel(WealthboxModel):
    @model_validator(mode="after")
    def ensure_any_field_present(self) -> "RequireAnyFieldModel":
        # Updates should allow explicit null for clearable fields while still
        # rejecting completely empty payloads.
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class PaginationQuery(WealthboxModel):
    page: int | None = Field(default=None, ge=1)
    per_page: int | None = Field(default=None, ge=1)


class EmailAddress(WealthboxModel):
    id: int | None = None
    address: str | None = None
    kind: str | None = None
    principal: bool | None = None
    destroy: bool | None = None


class PhoneNumber(WealthboxModel):
    id: int | None = None
    address: str | None = None
    kind: str | None = None
    principal: bool | None = None
    extension: str | None = None
    destroy: bool | None = None


class StreetAddress(WealthboxModel):
    id: int | None = None
    kind: str | None = None
    principal: bool | None = None
    street_line_1: str | None = None
    street_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    destroy: bool | None = None





class ContactRoleAssignment(WealthboxModel):
    id: int | None = None
    name: str | None = None


class LinkedToRef(WealthboxModel):
    id: int
    type: str = Field(description="Wealthbox object type, e.g. Contact, Opportunity")
