"""Wealthbox CRM tools — async HTTP client, Pydantic validation models, and CLI."""

from wealthbox_tools.client import WealthboxAPIError, WealthboxClient
from wealthbox_tools.models import (
    
    # Enums
    ContactTypeOptions,
    GenderOptions,
    MaritalStatusOptions,
    ContactSourceOptions,
    RecordTypeOptions,
    
    ActivityListQuery,
    ContactCreateInput,
    ContactListQuery,
    ContactUpdateInput,
    CustomFieldsListQuery,
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
    "ContactTypeOptions",
    "GenderOptions",
    "MaritalStatusOptions",
    "ContactSourceOptions",
    "RecordTypeOptions",


    "WealthboxClient",
    "WealthboxAPIError",
    "ActivityListQuery",
    "ContactCreateInput",
    "ContactListQuery",
    "ContactUpdateInput",
    "CustomFieldsListQuery",
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
