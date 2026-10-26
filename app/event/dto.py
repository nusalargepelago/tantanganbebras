"""Event input DTOs — admin CRUD and student attempt payloads."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import field_validator, model_validator

from framework.base import DTOBase

Category = Literal["cub", "scout", "rover"]


class EventCreateIn(DTOBase):
    """Validate an event creation payload."""

    event_name: str = DTOBase.field(..., alias="eventName", max_length=255)
    event_deadline: datetime = DTOBase.field(..., alias="eventDeadline")
    category: Category = DTOBase.field(...)
    time_limit: int = DTOBase.field(60, alias="timeLimit", ge=1, le=600)
    questions_id: list[str] = DTOBase.field(..., alias="questionsId")
    published: bool = DTOBase.field(False)
    description: str | None = DTOBase.field(None)

    @field_validator("event_name")
    @classmethod
    def check_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("required")
        return v.strip()

    @field_validator("questions_id")
    @classmethod
    def check_questions(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("list_required")
        stripped = [q.strip() for q in v]
        if any(not q for q in stripped):
            raise ValueError("items_must_be_non_empty_strings")
        if len(set(stripped)) != len(stripped):
            raise ValueError("must_be_unique")
        return stripped


class EventUpdateIn(DTOBase):
    """Validate an event update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    event_name: str | None = DTOBase.field(None, alias="eventName", max_length=255)
    event_deadline: datetime | None = DTOBase.field(None, alias="eventDeadline")
    category: Category | None = DTOBase.field(None)
    time_limit: int | None = DTOBase.field(None, alias="timeLimit", ge=1, le=600)
    questions_id: list[str] | None = DTOBase.field(None, alias="questionsId")
    published: bool | None = DTOBase.field(None)
    description: str | None = DTOBase.field(None)

    @field_validator("event_name")
    @classmethod
    def check_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("required")
        return v.strip()

    @field_validator("questions_id")
    @classmethod
    def check_questions(cls, v: list[str] | None) -> list[str] | None:
        if v is None or not v:
            return v
        stripped = [q.strip() for q in v]
        if any(not q for q in stripped):
            raise ValueError("items_must_be_non_empty_strings")
        if len(set(stripped)) != len(stripped):
            raise ValueError("must_be_unique")
        return stripped

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


class EventAnswerItem(DTOBase):
    """One submitted event answer."""

    event_question_id: str = DTOBase.field(..., alias="eventQuestionId")
    answer: str | None = DTOBase.field(None)


class EventAnswerTempIn(DTOBase):
    """Validate an event autosave payload."""

    event_student_name: str | None = DTOBase.field(None, alias="eventStudentName")
    event_question_id: str | None = DTOBase.field(None, alias="eventQuestionId")
    answer: str | None = DTOBase.field(None)

    @model_validator(mode="after")
    def check_target(self):
        if not self.event_student_name:
            raise ValueError("must_specify_practice_or_event_student")
        if not self.event_question_id:
            raise ValueError("must_specify_question_id")
        return self


class EventSubmitIn(DTOBase):
    """Validate an event submit payload."""

    event_student_name: str | None = DTOBase.field(None, alias="eventStudentName")
    answers: list[EventAnswerItem] | None = DTOBase.field(None)

    @model_validator(mode="after")
    def check_target(self):
        if not self.event_student_name:
            raise ValueError("must_specify_practice_or_event_student")
        if not self.answers:
            raise ValueError("answers_required")
        return self


__all__ = [
    "Category",
    "EventAnswerItem",
    "EventAnswerTempIn",
    "EventCreateIn",
    "EventSubmitIn",
    "EventUpdateIn",
]
