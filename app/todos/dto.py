"""Todo input DTOs — validation for todo create/update."""
from __future__ import annotations

from datetime import date

from pydantic import field_validator, model_validator

from framework.base import DTOBase


def _parse_due(value):
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError as exc:
            raise ValueError("invalid_date") from exc
    raise ValueError("invalid_date")


class TodoCreateIn(DTOBase):
    """Validate a todo creation payload."""

    title: str = DTOBase.field(..., min_length=1, max_length=255)
    description: str | None = DTOBase.field(None)
    completed: bool = DTOBase.field(False)
    due_date: date | None = DTOBase.field(None, alias="dueDate")

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_due(cls, value):
        return _parse_due(value)

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("required")
        return v.strip()


class TodoUpdateIn(DTOBase):
    """Validate a todo update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    title: str | None = DTOBase.field(None, min_length=1, max_length=255)
    description: str | None = DTOBase.field(None)
    completed: bool | None = DTOBase.field(None)
    due_date: date | None = DTOBase.field(None, alias="dueDate")

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_due(cls, value):
        return _parse_due(value)

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str | None) -> str:
        if v is None or not v.strip():
            raise ValueError("required")
        return v.strip()

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


__all__ = ["TodoCreateIn", "TodoUpdateIn"]
