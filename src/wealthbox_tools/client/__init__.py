from __future__ import annotations

from .base import WealthboxAPIError, _WealthboxBase
from .activity import ActivityMixin
from .categories import CategoriesMixin
from .contacts import ContactsMixin
from .events import EventsMixin
from .households import HouseholdsMixin
from .me import MeMixin
from .notes import NotesMixin
from .tasks import TasksMixin
from .users import UsersMixin



class WealthboxClient(
    ActivityMixin,
    CategoriesMixin,
    ContactsMixin,
    EventsMixin,
    HouseholdsMixin,
    MeMixin,
    NotesMixin,
    TasksMixin,
    UsersMixin,
    
    _WealthboxBase,
):
    """Async Wealthbox CRM API client.

    Usage::

        async with WealthboxClient() as client:
            me = await client.get_me()
            contacts = await client.list_contacts()
    """


__all__ = ["WealthboxClient", "WealthboxAPIError"]
