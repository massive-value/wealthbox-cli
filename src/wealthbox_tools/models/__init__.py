"""Pydantic models for Wealthbox tool payload/query validation."""

from .activity import ActivityListQuery
from .enums import (
    RecordTypeOptions,
    GenderOptions,
    MaritalStatusOptions,
    EventsOrderOptions,
    HouseholdTitleOptions,
    DocumentTypeOptions,
    ContactsOrderOptions,
    ActivityTypeOptions,
    CategoryTypeOptions,
)
from .common import (
    ContactRoleAssignment,
    EmailAddress,
    LinkedToRef,
    PhoneNumber,
    StreetAddress,
)
from .contacts import ContactCreateInput, ContactListQuery, ContactUpdateInput
from .events import EventCreateInput, EventListQuery, EventUpdateInput
from .households import HouseholdMemberInput
from .custom_fields import CustomFieldsListQuery, CustomFieldValue
from .notes import NoteCreateInput, NoteListQuery, NoteUpdateInput
from .tasks import TaskCreateInput, TaskListQuery, TaskUpdateInput


__all__ = [
    # Enums
    "RecordTypeOptions",
    "GenderOptions",
    "MaritalStatusOptions",
    "EventsOrderOptions",
    "HouseholdTitleOptions",
    "DocumentTypeOptions",
    "ContactsOrderOptions",
    "ActivityTypeOptions",
    "CategoryTypeOptions",

    # Activity
    "ActivityListQuery",

    # Contacts
    "ContactCreateInput",
    "ContactListQuery",
    "ContactUpdateInput",
    "ContactRoleAssignment",
    "EmailAddress",
    "LinkedToRef",
    "PhoneNumber",
    "StreetAddress",   

    # Events
    "EventCreateInput",
    "EventListQuery",
    "EventUpdateInput",

    # Households
    "HouseholdMemberInput",

    # Custom Fields
    "CustomFieldsListQuery",
    "CustomFieldValue",

    # Notes
    "NoteCreateInput",
    "NoteListQuery",
    "NoteUpdateInput",

    # Tasks
    "TaskCreateInput",
    "TaskListQuery",
    "TaskUpdateInput",
]
