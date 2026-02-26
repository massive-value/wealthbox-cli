from __future__ import annotations

from .base import WealthboxAPIError, _WealthboxBase
from .contacts import ContactsMixin
from .events import EventsMixin
from .notes import NotesMixin
from .households import HouseholdsMixin
from .readonly import ReadOnlyMixin
from .tasks import TasksMixin


class WealthboxClient(
    ContactsMixin,
    TasksMixin,
    EventsMixin,
    NotesMixin,
    HouseholdsMixin,
    ReadOnlyMixin,
    _WealthboxBase,
):
    """Async Wealthbox CRM API client.

    Usage::

        async with WealthboxClient() as client:
            me = await client.get_me()
            contacts = await client.list_contacts()
    """


__all__ = ["WealthboxClient", "WealthboxAPIError"]
