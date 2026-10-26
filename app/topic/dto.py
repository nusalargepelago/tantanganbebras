"""Topic input DTOs — validation for topic create, update, and reorder."""
from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from framework.base import DTOBase

Category = Literal["cub", "scout", "rover"]


class TopicCreateIn(DTOBase):
    """Validate a topic creation payload."""

    title: str = DTOBase.field(..., min_length=1, max_length=255)
    category: Category = DTOBase.field(...)
    idx: int = DTOBase.field(0, ge=0)


class TopicUpdateIn(DTOBase):
    """Validate a topic update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    title: str | None = DTOBase.field(None, min_length=1, max_length=255)
    category: Category | None = DTOBase.field(None)
    idx: int | None = DTOBase.field(None, ge=0)

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


class ReorderItem(DTOBase):
    """One topic reorder entry."""

    name: str
    idx: int


class TopicReorderIn(DTOBase):
    """Validate the raw reorder body before it reaches the service."""

    items: list[ReorderItem] | None = DTOBase.field(None, validate_default=True)

    @field_validator("items", mode="before")
    @classmethod
    def check_items(cls, v):
        if not isinstance(v, list):
            raise ValueError("must_be_list")
        checked = []
        for element in v:
            if not isinstance(element, dict):
                raise ValueError("malformed")
            name = element.get("name")
            idx = element.get("idx")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("name_required")
            if type(idx) is not int or idx < 0:
                raise ValueError("idx_invalid")
            checked.append(ReorderItem(name=name, idx=idx))
        return checked


__all__ = ["ReorderItem", "TopicCreateIn", "TopicReorderIn", "TopicUpdateIn"]
