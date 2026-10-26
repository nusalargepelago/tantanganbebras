"""Question input DTOs — validation for question create and update."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import field_validator, model_validator

from app.infra.enums import OPTION_LETTERS
from framework.base import DTOBase
from framework.exceptions import ValidationFailed

QuestionType = Literal["Multiple Choice", "Essay"]
Difficulty = Literal["Easy", "Medium", "Hard"]
Status = Literal["Active", "Inactive"]
Category = Literal["cub", "scout", "rover"]

_HTML_TAG = re.compile(r"<[^>]*>")
_HTML_IMG = re.compile(r"<img\b", re.IGNORECASE)
_HTML_BLANK = re.compile(r"&nbsp;|&#160;|&#xa0;", re.IGNORECASE)


def has_rich_content(value: str | None) -> bool:
    """True when HTML holds visible text or an image; mirrors the frontend helper."""
    if not value:
        return False
    if _HTML_IMG.search(value):
        return True
    text = _HTML_BLANK.sub(" ", _HTML_TAG.sub("", value)).replace("\u00a0", " ")
    return bool(text.strip())


def check_question_business(
    question_type: str,
    option_a: str | None,
    option_b: str | None,
    option_c: str | None,
    option_d: str | None,
    correct_answer: str | None,
    reference_answer: str | None,
) -> None:
    """Enforce MC/Essay consistency. Shared by create DTO and update service."""
    if question_type == "Multiple Choice":
        for letter, value in zip(
            OPTION_LETTERS, (option_a, option_b, option_c, option_d), strict=True
        ):
            if not has_rich_content(value):
                raise ValidationFailed(f"value_pg_requires_option_{letter}")
        if not correct_answer:
            raise ValidationFailed("value_pg_requires_correct_answer")
    elif not has_rich_content(reference_answer):
        raise ValidationFailed("value_essay_requires_reference_answer")


class QuestionCreateIn(DTOBase):
    """Validate a question creation payload."""

    question_code: str = DTOBase.field("Mini Challenge", alias="questionCode", max_length=40)
    question: str = DTOBase.field(...)
    description: str | None = DTOBase.field(None)
    question_type: QuestionType = DTOBase.field("Multiple Choice", alias="questionType")
    option_a: str | None = DTOBase.field(None, alias="optionA")
    option_b: str | None = DTOBase.field(None, alias="optionB")
    option_c: str | None = DTOBase.field(None, alias="optionC")
    option_d: str | None = DTOBase.field(None, alias="optionD")
    reference_answer: str | None = DTOBase.field(None, alias="referenceAnswer")
    correct_answer: str | None = DTOBase.field(None, alias="correctAnswer")
    category: Category = DTOBase.field(...)
    difficulty_level: Difficulty = DTOBase.field("Easy", alias="difficultyLevel")
    status: Status = DTOBase.field("Active")
    topic_id: str | None = DTOBase.field(None, alias="topicId", max_length=140)

    @field_validator("question_code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        v = v.strip()
        return v or "Mini Challenge"

    @field_validator("question")
    @classmethod
    def check_question(cls, v: str) -> str:
        if not has_rich_content(v):
            raise ValueError("required")
        return v

    @field_validator("description")
    @classmethod
    def normalize_description(cls, v: str | None) -> str | None:
        if not has_rich_content(v):
            return None
        return v

    @field_validator("correct_answer")
    @classmethod
    def normalize_correct(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if v == "":
            return None
        if v not in OPTION_LETTERS:
            raise ValueError("must_be_a_b_c_or_d")
        return v

    @model_validator(mode="after")
    def check_business(self):
        check_question_business(
            self.question_type,
            self.option_a,
            self.option_b,
            self.option_c,
            self.option_d,
            self.correct_answer,
            self.reference_answer,
        )
        return self


class QuestionUpdateIn(DTOBase):
    """Validate a question update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    question_code: str | None = DTOBase.field(None, alias="questionCode", max_length=40)
    question: str | None = DTOBase.field(None)
    description: str | None = DTOBase.field(None)
    question_type: QuestionType | None = DTOBase.field(None, alias="questionType")
    option_a: str | None = DTOBase.field(None, alias="optionA")
    option_b: str | None = DTOBase.field(None, alias="optionB")
    option_c: str | None = DTOBase.field(None, alias="optionC")
    option_d: str | None = DTOBase.field(None, alias="optionD")
    reference_answer: str | None = DTOBase.field(None, alias="referenceAnswer")
    correct_answer: str | None = DTOBase.field(None, alias="correctAnswer")
    category: Category | None = DTOBase.field(None)
    difficulty_level: Difficulty | None = DTOBase.field(None, alias="difficultyLevel")
    status: Status | None = DTOBase.field(None)
    topic_id: str | None = DTOBase.field(None, alias="topicId", max_length=140)

    @field_validator("question_code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or "Mini Challenge"

    @field_validator("question")
    @classmethod
    def check_question(cls, v: str | None) -> str:
        if not has_rich_content(v):
            raise ValueError("required")
        return v

    @field_validator("description")
    @classmethod
    def normalize_description(cls, v: str | None) -> str | None:
        if not has_rich_content(v):
            return None
        return v

    @field_validator("correct_answer")
    @classmethod
    def normalize_correct(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if v == "":
            return None
        if v not in OPTION_LETTERS:
            raise ValueError("must_be_a_b_c_or_d")
        return v

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


__all__ = [
    "Category",
    "Difficulty",
    "QuestionCreateIn",
    "QuestionType",
    "QuestionUpdateIn",
    "Status",
    "check_question_business",
    "has_rich_content",
]
