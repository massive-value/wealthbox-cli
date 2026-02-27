from __future__ import annotations

from typing import Literal
from enum import StrEnum


# Strict enum types — values fixed by Wealthbox, not configurable per account
RecordTypeOptions = Literal["Person", "Household", "Organization", "Trust"]
GenderOptions = Literal["Female", "Male", "Non-binary", "Unknown"]
MaritalStatusOptions = Literal["Married", "Single", "Divorced", "Widowed", "Life Partner", "Separated", "Unknown"]
DocumentTypeOptions = Literal[ "Contact", "Opportunity", "Project", "Task", "Event", "ManualInvestmentAccount", "DataFile" ]
HouseholdTitleOptions = Literal[ "Head", "Spouse", "Child", "Other Dependent", "Partner", "Parent", "Sibling", "Grandparent", "Grandchild" ]
ActivityTypeOptions = Literal [ "Contact", "StatusUpdate", "DropboxEmail", "PhoneCall", "Task", "Event", "Workflow", "WorkflowStep", "Opportunity", "DataFile", "MailMerge", "Project", "User", "Meeting", "CustomObject" ]

CategoryTypeOptions = Literal [ "tags", "custom_fields", "opportunity_stages", "opportunity_pipelines", "contact_types", "contact_sources", "task_categories", "event_categories", "file_categories", "investment_objectives", "financial_account_types", "email_types", "phone_types", "address_types", "website_types", "contact_roles" ]

ContactsOrderOptions = Literal[ "asc", "desc", "recent", "created", "updated" ]
EventsOrderOptions = Literal[ "asc", "desc", "recent", "created" ]



NotesOrderOptions = Literal[ "asc", "created", "updated" ]
EventsStateOptions = Literal[ "unconfirmed", "confirmed", "tentative", "completed", "cancelled" ]
EmailInviteeTypeOptions = Literal[ "User", "Contact" ]

# Tasks
class TaskFrame(StrEnum):
    TODAY = "today"
    TOMORROW = "tomorrow"
    THIS_WEEK = "this_week"
    NEXT_WEEK = "next_week"
    FUTURE = "future"
    SPECIFIC = "specific"


class TaskResourceType(StrEnum):
    CONTACT = "Contact"
    PROJECT = "Project"
    OPPORTUNITY = "Opportunity"


class TaskType(StrEnum):
    ALL = "all"
    PARENTS = "parents"
    SUBTASKS = "subtasks"


class TaskPriority(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"