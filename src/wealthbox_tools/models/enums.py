from __future__ import annotations

from enum import StrEnum


# Contacts
class RecordType(StrEnum):
    PERSON = "Person"
    HOUSEHOLD = "Household"
    ORGANIZATION = "Organization"
    TRUST = "Trust"


class Gender(StrEnum):
    FEMALE = "Female"
    MALE = "Male"
    NON_BINARY = "Non-binary"
    UNKNOWN = "Unknown"


class MaritalStatus(StrEnum):
    MARRIED = "Married"
    SINGLE = "Single"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"
    LIFE_PARTNER = "Life partner"
    SEPARATED = "Separated"
    UNKNOWN = "Unknown"

class ContactsOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"
    RECENT = "recent"
    CREATED = "created"
    UPDATED = "updated"


# Households
class HouseholdTitle(StrEnum):
    HEAD = "Head"
    SPOUSE = "Spouse"
    CHILD = "Child"
    OTHER_DEPENDENT = "Other Dependent"
    PARTNER = "Partner"
    PARENT = "Parent"
    SIBLING = "Sibling"
    GRANDPARENT = "Grandparent"
    GRANDCHILD = "Grandchild"


# Activity
class ActivityType(StrEnum):
    CONTACT = "Contact"
    STATUS_UPDATE = "StatusUpdate"
    DROPBOX_EMAIL = "DropboxEmail"
    PHONE_CALL = "PhoneCall"
    TASK = "Task"
    EVENT = "Event"
    WORKFLOW = "Workflow"
    WORKFLOW_STEP = "WorkflowStep"
    OPPORTUNITY = "Opportunity"
    DATA_FILE = "DataFile"
    MAIL_MERGE = "MailMerge"
    PROJECT = "Project"
    USER = "User"
    MEETING = "Meeting"
    CUSTOM_OBJECT = "CustomObject"


# Categories
class CategoryType(StrEnum):
    TAGS = "tags"
    CUSTOM_FIELDS = "custom_fields"
    OPPORTUNITY_STAGES = "opportunity_stages"
    OPPORTUNITY_PIPELINES = "opportunity_pipelines"
    CONTACT_TYPES = "contact_types"
    CONTACT_SOURCES = "contact_sources"
    TASK_CATEGORIES = "task_categories"
    EVENT_CATEGORIES = "event_categories"
    FILE_CATEGORIES = "file_categories"
    INVESTMENT_OBJECTIVES = "investment_objectives"
    FINANCIAL_ACCOUNT_TYPES = "financial_account_types"
    EMAIL_TYPES = "email_types"
    PHONE_TYPES = "phone_types"
    ADDRESS_TYPES = "address_types"
    WEBSITE_TYPES = "website_types"
    CONTACT_ROLES = "contact_roles"


class DocumentType(StrEnum):
    CONTACT = "Contact"
    OPPORTUNITY = "Opportunity"
    PROJECT = "Project"
    TASK = "Task"
    EVENT = "Event"
    MANUAL_INVESTMENT_ACCOUNT = "ManualInvestmentAccount"
    DATA_FILE = "DataFile"


# Events
class EventsState(StrEnum):
    UNCONFIRMED = "unconfirmed"
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventsOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"
    RECENT = "recent"
    CREATED = "created"


class EmailInviteeType(StrEnum):
    USER = "User"
    CONTACT = "Contact"


# Notes
class NotesOrder(StrEnum):
    ASC = "asc"
    CREATED = "created"
    UPDATED = "updated"


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