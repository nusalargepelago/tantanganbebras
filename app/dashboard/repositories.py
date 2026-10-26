"""Dashboard repositories — read-only aggregates across Tantangan Bebras domains."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, extract, func

from app.event.models import Event, EventAttempt, EventQuestion
from app.practice.models import Practice
from app.question.models import Question
from app.student.models import Student
from framework.extensions import db


class DashboardRepository:
    """Cross-domain read model for dashboard counters (never commits)."""

    def question_counts_by_category(self) -> dict[str, int]:
        rows = (
            db.session.query(Question.category, func.count())
            .group_by(Question.category)
            .all()
        )
        return dict(rows)

    def active_event_count(self) -> int:
        now = datetime.now(UTC)
        return (
            db.session.query(func.count(Event.id))
            .filter(Event.published.is_(True), Event.event_deadline >= now)
            .scalar()
            or 0
        )

    def student_status_counts(self) -> dict[str, int]:
        rows = db.session.query(Student.status, func.count()).group_by(Student.status).all()
        return dict(rows)

    def students_by_school(self) -> list[tuple[str, int]]:
        label = case(
            (Student.school.is_(None), "(No school)"),
            (Student.school == "", "(No school)"),
            else_=Student.school,
        )
        rows = (
            db.session.query(label, func.count())
            .group_by(label)
            .order_by(func.count().desc(), label.asc())
            .all()
        )
        return [(str(school), count) for school, count in rows]

    def students_by_year(self) -> list[tuple[int, int]]:
        year = extract("year", Student.created_at)
        rows = (
            db.session.query(year, func.count()).group_by(year).order_by(year.asc()).all()
        )
        return [(int(y), count) for y, count in rows]

    def student_totals(self) -> tuple[int, int]:
        total = db.session.query(func.count(Student.user_id)).scalar() or 0
        schools = (
            db.session.query(func.count(func.distinct(Student.school)))
            .filter(Student.school.isnot(None), Student.school != "")
            .scalar()
            or 0
        )
        return total, schools

    def student_category_counts(self) -> dict[str, int]:
        rows = (
            db.session.query(Student.category, func.count()).group_by(Student.category).all()
        )
        return dict(rows)

    def attempts_last_24h(self) -> int:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        return (
            db.session.query(func.count(EventAttempt.id))
            .filter(EventAttempt.created_at >= cutoff)
            .scalar()
            or 0
        )

    def recent_events(self, limit: int = 5) -> list[Event]:
        return (
            db.session.query(Event).order_by(Event.created_at.desc()).limit(limit).all()
        )

    def event_question_counts(self) -> dict[str, int]:
        rows = (
            db.session.query(EventQuestion.event_id, func.count())
            .group_by(EventQuestion.event_id)
            .all()
        )
        return dict(rows)

    def recent_students(self, limit: int = 5) -> list[Student]:
        return (
            db.session.query(Student)
            .order_by(Student.created_at.desc())
            .limit(limit)
            .all()
        )

    def practice_count(self, student_id: str) -> int:
        return (
            db.session.query(func.count(Practice.id))
            .filter(Practice.student_id == student_id)
            .scalar()
            or 0
        )

    def attempt_count(self, student_id: str) -> int:
        return (
            db.session.query(func.count(EventAttempt.id))
            .filter(EventAttempt.student_id == student_id)
            .scalar()
            or 0
        )

    def last_practice(self, student_id: str) -> Practice | None:
        return (
            db.session.query(Practice)
            .filter(Practice.student_id == student_id)
            .order_by(Practice.created_at.desc())
            .first()
        )

    def last_attempt(self, student_id: str) -> EventAttempt | None:
        return (
            db.session.query(EventAttempt)
            .filter(EventAttempt.student_id == student_id)
            .order_by(EventAttempt.created_at.desc())
            .first()
        )


__all__ = ["DashboardRepository"]
