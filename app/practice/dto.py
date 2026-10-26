"""Practice input DTOs — create query, autosave and submit payloads."""
from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from framework.base import DTOBase

Category = Literal["cub", "scout", "rover"]


class AnswerItem(DTOBase):
    """One submitted answer."""

    question_id: str = DTOBase.field(..., alias="questionId")
    answer: str | None = DTOBase.field(None)


class AnswerTempIn(DTOBase):
    """Validate an autosave payload."""

    practice_name: str | None = DTOBase.field(None, alias="practiceName")
    question_id: str | None = DTOBase.field(None, alias="questionId")
    answer: str | None = DTOBase.field(None)

    @model_validator(mode="after")
    def check_target(self):
        if not self.practice_name:
            raise ValueError("must_specify_practice_or_event_student")
        if not self.question_id:
            raise ValueError("must_specify_question_id")
        return self


class SubmitIn(DTOBase):
    """Validate a practice submit payload."""

    practice_name: str | None = DTOBase.field(None, alias="practiceName")
    answers: list[AnswerItem] | None = DTOBase.field(None)

    @model_validator(mode="after")
    def check_target(self):
        if not self.practice_name:
            raise ValueError("must_specify_practice_or_event_student")
        if not self.answers:
            raise ValueError("answers_required")
        return self


class CreateIn(DTOBase):
    """Validate the create query string — ``?test=1&category=cub``."""

    test: bool = DTOBase.field(False)
    category: Category | None = DTOBase.field(None)


class PracticeSettingsIn(DTOBase):
    """Validate a practice settings payload."""

    min_questions: int = DTOBase.field(..., alias="minQuestions", ge=1)


__all__ = ["AnswerItem", "AnswerTempIn", "CreateIn", "PracticeSettingsIn", "SubmitIn"]
