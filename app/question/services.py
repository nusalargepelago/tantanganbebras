"""Question services — business logic for the question bank."""
from __future__ import annotations

from datetime import UTC, datetime

from app.infra.audit import log as audit_log
from app.infra.naming import next_name, slugify
from app.question.dto import (
    QuestionCreateIn,
    QuestionUpdateIn,
    check_question_business,
)
from app.question.models import Question
from app.question.repositories import QuestionRepository
from app.topic.repositories import TopicRepository
from framework.base import ServiceBase
from framework.exceptions import NotFound

_FIELD_ALIASES = {
    "question_code": "question_code",
    "question": "question",
    "question_type": "question_type",
    "option_a": "option_a",
    "option_b": "option_b",
    "option_c": "option_c",
    "option_d": "option_d",
    "reference_answer": "reference_answer",
    "correct_answer": "correct_answer",
    "category": "category",
    "difficulty_level": "difficulty_level",
    "status": "status",
    "topic_id": "topic_id",
}


class QuestionService(ServiceBase[QuestionRepository]):
    """Business logic for questions."""

    repository_class = QuestionRepository

    def __init__(
        self,
        repo: QuestionRepository | None = None,
        topics: TopicRepository | None = None,
    ):
        super().__init__(repo)
        self._topics = topics or TopicRepository()

    def list_questions(self, **filters) -> tuple[list[Question], int]:
        return self._repo.list_questions(**filters)

    def get_question(self, name: str) -> Question:
        question = self._repo.find_by_name(name)
        if question is None:
            raise NotFound("question_not_found")
        return question

    def create_question(self, dto: QuestionCreateIn, *, actor_id: str) -> Question:
        if dto.topic_id and self._topics.find_by_name(dto.topic_id) is None:
            raise NotFound("topic_not_found")

        name = next_name(
            slugify(dto.question_code, fallback="mini-challenge"),
            self._repo.name_exists,
            year=True,
        )
        question = Question(
            name=name,
            question_code=dto.question_code,
            question=dto.question,
            description=dto.description,
            question_type=dto.question_type,
            option_a=dto.option_a,
            option_b=dto.option_b,
            option_c=dto.option_c,
            option_d=dto.option_d,
            reference_answer=dto.reference_answer,
            correct_answer=dto.correct_answer,
            category=dto.category,
            difficulty_level=dto.difficulty_level,
            status=dto.status,
            topic_id=dto.topic_id,
            creator_id=actor_id,
        )
        self._repo.add(question)
        audit_log(
            "question_created",
            user_id=actor_id,
            resource=f"question/{name}",
            details={"category": dto.category, "type": dto.question_type},
        )
        self._commit()
        return question

    def update_question(self, name: str, dto: QuestionUpdateIn, *, actor_id: str) -> Question:
        question = self.get_question(name)
        data = dto.model_dump(exclude_unset=True)
        if "topic_id" in data and data["topic_id"] and self._topics.find_by_name(data["topic_id"]) is None:
            raise NotFound("topic_not_found")

        merged = {
            field: data.get(field, getattr(question, field)) for field in _FIELD_ALIASES
        }
        check_question_business(
            merged["question_type"],
            merged["option_a"],
            merged["option_b"],
            merged["option_c"],
            merged["option_d"],
            merged["correct_answer"],
            merged["reference_answer"],
        )

        changed = []
        for field, value in data.items():
            setattr(question, field, value)
            changed.append(field)
        audit_log(
            "question_updated",
            user_id=actor_id,
            resource=f"question/{name}",
            details={"changed": sorted(changed)},
        )
        self._commit()
        return question

    def soft_delete(self, name: str, *, actor_id: str) -> None:
        question = self.get_question(name)
        question.disabled = True
        question.disabled_at = datetime.now(UTC)
        audit_log("question_soft_deleted", user_id=actor_id, resource=f"question/{name}")
        self._commit()

    def restore(self, name: str, *, actor_id: str) -> Question:
        question = self.get_question(name)
        question.disabled = False
        question.disabled_at = None
        audit_log("question_restored", user_id=actor_id, resource=f"question/{name}")
        self._commit()
        return question

    def purge(self, name: str, *, actor_id: str) -> None:
        question = self.get_question(name)
        self._repo.delete(question)
        audit_log("question_purged", user_id=actor_id, resource=f"question/{name}")
        self._commit()


__all__ = ["QuestionService"]
