from __future__ import annotations

from pydantic import model_validator

from .custom_fields import CustomFieldValue

from .common import (
    ContactRoleAssignment,
    EmailAddress,
    PaginationQuery,
    PhoneNumber,
    StreetAddress,
    WealthboxModel,
)

from .enums import (
    RecordType,
    Gender,
    MaritalStatus,
    HouseholdTitle,
    ContactsOrder,
)


class ContactListQuery(PaginationQuery):
    id: int | None = None
    contact_type: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    external_unique_id: str | None = None
    active: bool | None = None
    tags: list[str] | None = None
    deleted: bool | None = None
    deleted_since: str | None = None
    household_title: HouseholdTitle | None = None
    type: RecordType | None = None
    order: ContactsOrder | None = None
    updated_since: str | None = None
    updated_before: str | None = None
    


class ContactCreateInput(WealthboxModel):
    # Core identity
    type: RecordType | None = None
    prefix: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    suffix: str | None = None
    nickname: str | None = None
    name: str | None = None

    # Person/company attributes
    job_title: str | None = None
    company_name: str | None = None
    marital_status: MaritalStatus | None = None
    gender: Gender | None = None
    birth_date: str | None = None
    anniversary: str | None = None
    client_since: str | None = None
    date_of_death: str | None = None
    
    contact_type: str | None = None
    contact_source: str | None = None
    status: str | None = None
    assigned_to: int | None = None
    visible_to: str | None = None
    external_unique_id: str | None = None
    background_information: str | None = None
    important_information: str | None = None
    

    # Nested arrays
    email_addresses: list[EmailAddress] | None = None
    phone_numbers: list[PhoneNumber] | None = None
    street_addresses: list[StreetAddress] | None = None
    tags: list[str] | None = None
    custom_fields: list[CustomFieldValue] | None = None
    contact_roles: list[ContactRoleAssignment] | None = None


    @model_validator(mode="after")
    def ensure_non_empty_create(self) -> "ContactCreateInput":
        # Enforce non-empty payload for create only; update has its own rules.
        if type(self) is ContactCreateInput and not self.model_dump(exclude_none=True):
            raise ValueError("At least one field must be provided.")
        return self


class ContactUpdateInput(ContactCreateInput):
    destroy: bool | None = None

    @model_validator(mode="after")
    def ensure_non_empty_update(self) -> "ContactUpdateInput":
        # For updates, allow explicit nulls (field clearing) as long as at least
        # one field was actually provided by the caller.
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self
