from __future__ import annotations

from pydantic import Field, model_validator

from .common import WealthboxModel
from .enums import HouseholdTitleOptions


class HouseholdMemberInput(WealthboxModel):
    id: int | None = Field(default=None, ge=1)
    title: HouseholdTitleOptions | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def ensure_member_target(self) -> "HouseholdMemberInput":
        if self.id is None and self.title is None:
            raise ValueError("Either id or title must be provided.")
        return self
