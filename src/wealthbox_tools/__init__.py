"""Wealthbox CRM tools — async HTTP client, Pydantic validation models, and CLI."""

from wealthbox_tools.client import WealthboxAPIError, WealthboxClient
from wealthbox_tools.models import (

    # Enums
    Gender,
    MaritalStatus,
    RecordType,

    ActivityListQuery,
    ContactCreateInput,
    ContactListQuery,
    ContactUpdateInput,
    CategoryListQuery,
    EventCreateInput,
    EventListQuery,
    EventUpdateInput,
    HouseholdMemberInput,
    NoteCreateInput,
    NoteListQuery,
    NoteUpdateInput,
    TaskCreateInput,
    TaskListQuery,
    TaskUpdateInput,

)

__all__ = [

    # Enums
    "Gender",
    "MaritalStatus",
    "RecordType",


    "WealthboxClient",
    "WealthboxAPIError",
    "ActivityListQuery",
    "ContactCreateInput",
    "ContactListQuery",
    "ContactUpdateInput",
    "CategoryListQuery",
    "EventCreateInput",
    "EventListQuery",
    "EventUpdateInput",
    "HouseholdMemberInput",
    "NoteCreateInput",
    "NoteListQuery",
    "NoteUpdateInput",
    "TaskCreateInput",
    "TaskListQuery",
    "TaskUpdateInput",
]
