"""Pydantic models for Wealthbox tool payload/query validation."""

from .activity import ActivityListQuery
from .enums import (
    RecordType,
    Gender,
    MaritalStatus,
    EventsOrder,
    HouseholdTitle,
    DocumentType,
    ContactsOrder,
    ActivityType,
    CategoryType,
    NotesOrder,
    TaskResourceType,
    TaskFrame,
    TaskType,
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
from .custom_fields import CategoryListQuery, CustomFieldValue
from .notes import NoteCreateInput, NoteListQuery, NoteUpdateInput
from .tasks import TaskCreateInput, TaskListQuery, TaskUpdateInput


__all__ = [
    # Enums
    "RecordType",
    "Gender",
    "MaritalStatus",
    "EventsOrder",
    "HouseholdTitle",
    "DocumentType",
    "ContactsOrder",
    "ActivityType",
    "CategoryType",
    "NotesOrder",
    "TaskFrame",
    "TaskResourceType",
    "TaskType",

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

    # Categories
    "CategoryListQuery",
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
