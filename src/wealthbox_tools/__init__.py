"""Wealthbox CRM tools — async HTTP client, Pydantic validation models, and CLI."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("wealthbox-cli")
except PackageNotFoundError:  # pragma: no cover - editable / source-only path
    __version__ = "0.0.0"

from wealthbox_tools.client import WealthboxAPIError, WealthboxClient
from wealthbox_tools.models import (
    ActivityListQuery,
    CategoryListQuery,
    ContactCreateInput,
    ContactListQuery,
    ContactUpdateInput,
    EventCreateInput,
    EventListQuery,
    EventUpdateInput,
    # Enums
    Gender,
    HouseholdMemberInput,
    MaritalStatus,
    NoteCreateInput,
    NoteListQuery,
    NoteUpdateInput,
    RecordType,
    TaskCreateInput,
    TaskListQuery,
    TaskUpdateInput,
)

__all__ = [
    "__version__",

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
