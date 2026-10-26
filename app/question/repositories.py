"""Question repositories — query layer for the question bank."""
from __future__ import annotations

from app.question.models import Question
from framework.base import RepositoryBase
from framework.extensions import db


class QuestionRepository(RepositoryBase[Question]):
    """Query layer for questions."""

    model = Question

    def find_by_name(self, name: str) -> Question | None:
        return self.find_one(name=name)

    def name_exists(self, name: str) -> bool:
        return self.count(name=name) > 0

    def find_many_by_names(self, names: list[str]) -> list[Question]:
        if not names:
            return []
        return db.session.query(Question).filter(Question.name.in_(names)).all()

    def detach_topic(self, topic_name: str) -> None:
        db.session.query(Question).filter(Question.topic_id == topic_name).update(
            {"topic_id": None}, synchronize_session=False
        )

    def list_pool(self, *, category: str, status: str, limit: int) -> list[Question]:
        return (
            db.session.query(Question)
            .filter(
                Question.category == category,
                Question.status == status,
                Question.disabled.is_(False),
            )
            .order_by(Question.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_questions(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        difficulty_level: str | None = None,
        topic_id: str | None = None,
        q: str | None = None,
        include_disabled: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Question], int]:
        query = db.session.query(Question)
        if not include_disabled:
            query = query.filter(Question.disabled.is_(False))
        if category:
            query = query.filter(Question.category == category)
        if status:
            query = query.filter(Question.status == status)
        if difficulty_level:
            query = query.filter(Question.difficulty_level == difficulty_level)
        if topic_id:
            query = query.filter(Question.topic_id == topic_id)
        if q:
            like = f"%{q}%"
            query = query.filter(
                db.or_(
                    Question.question.ilike(like),
                    Question.description.ilike(like),
                    Question.question_code.ilike(like),
                )
            )
        total = query.count()
        items = (
            query.order_by(Question.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["QuestionRepository"]
