"""Pydantic models for Wealthbox tool payload/query validation."""

from .activity import ActivityListQuery
from .enums import (
    ContactTypeOptions,
    ContactSourceOptions,
    RecordTypeOptions,
    GenderOptions,
    MaritalStatusOptions,
    EventsOrderOptions,
    HouseholdTitleOptions,
    DocumentTypeOptions,
    ContactsOrderOptions,
)
from .common import (
    ContactRoleAssignment,
    CustomFieldValue,
    EmailAddress,
    LinkedToRef,
    PhoneNumber,
    StreetAddress,
)
from .contacts import ContactCreateInput, ContactListQuery, ContactUpdateInput
from .events import EventCreateInput, EventListQuery, EventUpdateInput
from .households import HouseholdMemberInput
from .custom_fields import CustomFieldsListQuery
from .notes import NoteCreateInput, NoteListQuery, NoteUpdateInput
from .tasks import TaskCreateInput, TaskListQuery, TaskUpdateInput

__all__ = [
    # Enums
    "ContactTypeOptions",
    "ContactSourceOptions",
    "RecordTypeOptions",
    "GenderOptions",
    "MaritalStatusOptions",
    "EventsOrderOptions",
    "HouseholdTitleOptions",
    "DocumentTypeOptions",
    "ContactsOrderOptions",

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
