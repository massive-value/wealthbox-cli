from __future__ import annotations

from pydantic import Field

from .common import LinkedToRef, PaginationQuery, RequireAnyFieldModel, WealthboxModel

from .enums import NotesOrder, NoteResourceType


class NoteListQuery(PaginationQuery):
    resource_id: int | None = None
    resource_type: NoteResourceType | None = None
    order: NotesOrder | None = None
    updated_since: str | None = None
    updated_before: str | None = None


class NoteCreateInput(WealthboxModel):
    content: str = Field(min_length=1)
    linked_to: list[LinkedToRef] | None = None
    # visable_to: str | None = None
    # tags: list[str] | None = None


class NoteUpdateInput(RequireAnyFieldModel):
    content: str | None = Field(default=None, min_length=1)
    linked_to: list[LinkedToRef] | None = None
    # visable_to: str | None = None
    # tags: list[str] | None = None
