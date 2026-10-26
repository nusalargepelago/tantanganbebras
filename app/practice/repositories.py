"""Practice repositories — query layer for practice sheets and children."""
from __future__ import annotations

from app.practice.models import (
    Practice,
    PracticeAnswer,
    PracticeAnswerTemp,
    PracticeBeforeShuffle,
    PracticeQuestion,
)
from framework.base import RepositoryBase
from framework.extensions import db


class PracticeRepository(RepositoryBase[Practice]):
    """Query layer for practices (children keyed by ``practices.name``)."""

    model = Practice

    def find_by_name(self, name: str) -> Practice | None:
        return self.find_one(name=name)

    def active_for_student(self, student_id: str) -> Practice | None:
        return (
            db.session.query(Practice)
            .filter(
                Practice.student_id == student_id,
                Practice.finished_at.is_(None),
            )
            .order_by(Practice.created_at.desc())
            .first()
        )

    def list_for_student(self, student_id: str, *, limit: int = 100) -> list[Practice]:
        return (
            db.session.query(Practice)
            .filter(
                Practice.student_id == student_id,
                ~Practice.name.like("test-%"),
            )
            .order_by(Practice.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_all(
        self,
        *,
        category: str | None = None,
        student_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Practice], int]:
        query = db.session.query(Practice).filter(~Practice.name.like("test-%"))
        if category:
            query = query.filter(Practice.category == category)
        if student_id:
            query = query.filter(Practice.student_id == student_id)
        total = query.count()
        items = (
            query.order_by(Practice.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def get_questions(self, practice_name: str) -> list[PracticeQuestion]:
        return (
            db.session.query(PracticeQuestion)
            .filter(PracticeQuestion.practice_id == practice_name)
            .order_by(PracticeQuestion.shuffled_idx)
            .all()
        )

    def get_before_shuffle(self, practice_name: str) -> list[PracticeBeforeShuffle]:
        return (
            db.session.query(PracticeBeforeShuffle)
            .filter(PracticeBeforeShuffle.practice_id == practice_name)
            .order_by(PracticeBeforeShuffle.original_idx)
            .all()
        )

    def get_answers(self, practice_name: str) -> list[PracticeAnswer]:
        return db.session.query(PracticeAnswer).filter(
            PracticeAnswer.practice_id == practice_name
        ).all()

    def get_temps(self, practice_name: str) -> list[PracticeAnswerTemp]:
        return db.session.query(PracticeAnswerTemp).filter(
            PracticeAnswerTemp.practice_id == practice_name
        ).all()

    def find_temp(self, practice_name: str, question_id: str) -> PracticeAnswerTemp | None:
        return db.session.query(PracticeAnswerTemp).filter(
            PracticeAnswerTemp.practice_id == practice_name,
            PracticeAnswerTemp.question_id == question_id,
        ).first()

    def delete_test_practices(self, student_id: str) -> None:
        names = [
            row[0]
            for row in db.session.query(Practice.name).filter(
                Practice.student_id == student_id,
                Practice.name.like("test-%"),
            )
        ]
        if not names:
            return
        for child in (
            PracticeAnswer,
            PracticeAnswerTemp,
            PracticeBeforeShuffle,
            PracticeQuestion,
        ):
            db.session.query(child).filter(child.practice_id.in_(names)).delete(
                synchronize_session=False
            )
        db.session.query(Practice).filter(Practice.name.in_(names)).delete(
            synchronize_session=False
        )


__all__ = ["PracticeRepository"]
