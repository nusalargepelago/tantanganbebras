"""Question presenters — wire serialization for questions."""
from __future__ import annotations

from app.infra.presenters import UtcPresenterBase
from app.question.models import Question
from framework.base import PresenterBase


class QuestionOut(UtcPresenterBase):
    """Question on the wire."""

    name: str
    question_code: str = PresenterBase.field("Mini Challenge", alias="questionCode")
    question: str
    description: str | None = PresenterBase.field(None)
    question_type: str = PresenterBase.field("Multiple Choice", alias="questionType")
    option_a: str | None = PresenterBase.field(None, alias="optionA")
    option_b: str | None = PresenterBase.field(None, alias="optionB")
    option_c: str | None = PresenterBase.field(None, alias="optionC")
    option_d: str | None = PresenterBase.field(None, alias="optionD")
    reference_answer: str | None = PresenterBase.field(None, alias="referenceAnswer")
    correct_answer: str | None = PresenterBase.field(None, alias="correctAnswer")
    category: str
    difficulty_level: str = PresenterBase.field("Easy", alias="difficultyLevel")
    status: str = PresenterBase.field("Active")
    creator_id: str | None = PresenterBase.field(None, alias="creatorId")
    topic_id: str | None = PresenterBase.field(None, alias="topicId")
    disabled: bool = PresenterBase.field(False)
    disabled_at: str | None = PresenterBase.field(None, alias="disabledAt")
    created_at: str | None = PresenterBase.field(None, alias="createdAt")
    updated_at: str | None = PresenterBase.field(None, alias="updatedAt")

    @classmethod
    def from_question(cls, question: Question) -> QuestionOut:
        return cls.from_model(question)

    @classmethod
    def list_row(cls, question: Question) -> dict:
        """List payloads drop the description; the editor fetches it per question."""
        row = cls.from_question(question).to_dict()
        row.pop("description", None)
        return row


__all__ = ["QuestionOut"]
