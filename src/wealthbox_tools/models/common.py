from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, AfterValidator


# ---------------------------------------------------------------------------
# Reusable date / datetime validators
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
# ISO 8601 datetime: YYYY-MM-DDTHH:MM:SS with optional Z or ±HH:MM offset
_DATETIME_ISO_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?$')
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

_LINKED_TO_TYPES = frozenset({"Contact", "Project", "Opportunity"})
_LINKED_TO_TYPES_DISPLAY = ", ".join(sorted(_LINKED_TO_TYPES))

_DATETIME_EXAMPLE = "e.g. '2026-04-01T10:00:00-07:00' or '2026-04-01T10:00:00Z'"


def _check_date(v: str | None) -> str | None:
    if v is not None and not _DATE_RE.match(v):
        raise ValueError("must be in YYYY-MM-DD format (e.g. '1975-10-27')")
    return v


def _check_datetime(v: str | None) -> str | None:
    if v is not None and not _DATETIME_ISO_RE.match(v):
        raise ValueError(f"must be ISO 8601 datetime ({_DATETIME_EXAMPLE})")
    return v


def _check_email(v: str | None) -> str | None:
    if v is not None and not _EMAIL_RE.match(v):
        raise ValueError(f"'{v}' is not a valid email address")
    return v


# Annotated type aliases — use these as field type annotations so format
# validation is applied automatically. Import into each model module that uses them.
DateField = Annotated[str | None, AfterValidator(_check_date)]
DateTimeField = Annotated[str | None, AfterValidator(_check_datetime)]
# For required (non-optional) datetime string fields.
NonNullDateTimeField = Annotated[str, AfterValidator(_check_datetime)]
EmailField = Annotated[str | None, AfterValidator(_check_email)]


# ---------------------------------------------------------------------------
# Base models
# ---------------------------------------------------------------------------

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
    per_page: int | None = Field(default=25, ge=1, le=100)


# ---------------------------------------------------------------------------
# Nested contact sub-objects
# ---------------------------------------------------------------------------

class EmailAddress(WealthboxModel):
    id: int | None = Field(default=None, ge=1)
    address: EmailField = None
    kind: str | None = None
    principal: bool | None = None
    destroy: bool | None = None


class PhoneNumber(WealthboxModel):
    id: int | None = Field(default=None, ge=1)
    address: str | None = None
    kind: str | None = None
    principal: bool | None = None
    extension: str | None = None
    destroy: bool | None = None


class StreetAddress(WealthboxModel):
    id: int | None = Field(default=None, ge=1)
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
    id: int | None = Field(default=None, ge=1)
    type: str | None = None


class LinkedToRef(WealthboxModel):
    id: int = Field(ge=1, description="Wealthbox object ID (positive integer)")
    type: str = Field(description="Wealthbox object type; allowed: Contact, Project, Opportunity")

    @field_validator("type")
    @classmethod
    def validate_linked_to_type(cls, v: str) -> str:
        if v not in _LINKED_TO_TYPES:
            raise ValueError(
                f"'{v}' is not a valid linked_to type; must be one of: {_LINKED_TO_TYPES_DISPLAY}"
            )
        return v
