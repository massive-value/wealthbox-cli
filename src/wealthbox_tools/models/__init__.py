"""Pydantic models for Wealthbox tool payload/query validation."""

from .activity import ActivityListQuery
from .comments import CommentListQuery
from .enums import (
    RecordType,
    Gender,
    MaritalStatus,
    EventsOrder,
    EventsState,
    HouseholdTitle,
    DocumentType,
    ContactsOrder,
    ActivityType,
    CategoryType,
    NotesOrder,
    NoteResourceType,
    TaskResourceType,
    TaskFrame,
    TaskPriority,
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
    "NoteResourceType",
    "TaskFrame",
    "TaskPriority",
    "TaskResourceType",
    "TaskType",
    "EventsState",

    # Activity
    "ActivityListQuery",

    # Comments
    "CommentListQuery",

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
