from __future__ import annotations

from .activity import ActivityMixin
from .base import WealthboxAPIError, _WealthboxBase
from .categories import CategoriesMixin
from .comments import CommentsMixin
from .contacts import ContactsMixin
from .events import EventsMixin
from .households import HouseholdsMixin
from .me import MeMixin
from .notes import NotesMixin
from .opportunities import OpportunitiesMixin
from .projects import ProjectsMixin
from .tasks import TasksMixin
from .users import UsersMixin
from .workflows import WorkflowsMixin


class WealthboxClient(
    ActivityMixin,
    CategoriesMixin,
    CommentsMixin,
    ContactsMixin,
    EventsMixin,
    HouseholdsMixin,
    MeMixin,
    NotesMixin,
    OpportunitiesMixin,
    ProjectsMixin,
    TasksMixin,
    UsersMixin,
    WorkflowsMixin,
    _WealthboxBase,
):
    """Async Wealthbox CRM API client.

    Usage::

        async with WealthboxClient() as client:
            me = await client.get_me()
            contacts = await client.list_contacts()
    """


__all__ = ["WealthboxClient", "WealthboxAPIError"]
