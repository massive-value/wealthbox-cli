"""Pydantic models for Wealthbox tool payload/query validation."""

from .activity import ActivityListQuery
from .comments import CommentListQuery
from .common import (
    ContactRoleAssignment,
    EmailAddress,
    LinkedToRef,
    PhoneNumber,
    StreetAddress,
)
from .contacts import ContactCreateInput, ContactListQuery, ContactUpdateInput
from .custom_fields import CategoryListQuery, CustomFieldValue
from .enums import (
    ActivityType,
    CategoryType,
    CommentResourceType,
    ContactsOrder,
    DocumentType,
    EventsOrder,
    EventsState,
    Gender,
    HouseholdTitle,
    MaritalStatus,
    NoteResourceType,
    NotesOrder,
    OpportunityAmountKind,
    OpportunityOrder,
    OpportunityResourceType,
    RecordType,
    TaskFrame,
    TaskPriority,
    TaskResourceType,
    TaskType,
    WorkflowResourceType,
    WorkflowStatus,
)
from .events import EventCreateInput, EventListQuery, EventUpdateInput
from .households import HouseholdMemberInput
from .notes import NoteCreateInput, NoteListQuery, NoteUpdateInput
from .opportunities import OpportunityAmount, OpportunityCreateInput, OpportunityListQuery, OpportunityUpdateInput
from .projects import ProjectCreateInput, ProjectListQuery, ProjectUpdateInput
from .tasks import TaskCreateInput, TaskListQuery, TaskUpdateInput
from .workflows import (
    WorkflowCreateInput,
    WorkflowListQuery,
    WorkflowMilestone,
    WorkflowStepCompleteInput,
    WorkflowStepRevertInput,
    WorkflowTemplateListQuery,
)

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
    "CommentResourceType",
    "NotesOrder",
    "NoteResourceType",
    "OpportunityAmountKind",
    "OpportunityOrder",
    "OpportunityResourceType",
    "TaskFrame",
    "TaskPriority",
    "TaskResourceType",
    "TaskType",
    "EventsState",
    "WorkflowResourceType",
    "WorkflowStatus",

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

    # Opportunities
    "OpportunityAmount",
    "OpportunityCreateInput",
    "OpportunityListQuery",
    "OpportunityUpdateInput",

    # Projects
    "ProjectCreateInput",
    "ProjectListQuery",
    "ProjectUpdateInput",

    # Tasks
    "TaskCreateInput",
    "TaskListQuery",
    "TaskUpdateInput",

    # Workflows
    "WorkflowCreateInput",
    "WorkflowListQuery",
    "WorkflowMilestone",
    "WorkflowStepCompleteInput",
    "WorkflowStepRevertInput",
    "WorkflowTemplateListQuery",
]
