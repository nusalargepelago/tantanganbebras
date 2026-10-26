"""Event repositories — query layer for events, pivots, and attempts."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func

from app.event.models import (
    Event,
    EventAttempt,
    EventAttemptAnswer,
    EventAttemptAnswerTemp,
    EventAttemptQuestion,
    EventQuestion,
)
from framework.base import RepositoryBase
from framework.extensions import db


class EventRepository(RepositoryBase[Event]):
    """Query layer for events and their question pivots."""

    model = Event

    def find_by_name(self, name: str) -> Event | None:
        return self.find_one(name=name)

    def name_exists(self, name: str) -> bool:
        return self.count(name=name) > 0

    def list_all(
        self,
        *,
        category: str | None = None,
        published: bool | None = None,
        include_disabled: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Event], int]:
        query = db.session.query(Event)
        if not include_disabled:
            query = query.filter(Event.disabled.is_(False))
        if category:
            query = query.filter(Event.category == category)
        if published is not None:
            query = query.filter(Event.published.is_(published))
        total = query.count()
        items = (
            query.order_by(Event.event_deadline.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def candidates(self, *, limit: int = 500) -> list[Event]:
        now = datetime.now(UTC)
        return (
            db.session.query(Event)
            .filter(
                Event.published.is_(True),
                Event.disabled.is_(False),
                Event.event_deadline >= now,
            )
            .order_by(Event.event_deadline.desc())
            .limit(limit)
            .all()
        )

    def get_question_counts(self) -> dict[str, int]:
        rows = (
            db.session.query(EventQuestion.event_id, func.count())
            .group_by(EventQuestion.event_id)
            .all()
        )
        return {event_id: count for event_id, count in rows}

    def get_questions(self, event_name: str) -> list[EventQuestion]:
        return (
            db.session.query(EventQuestion)
            .filter(EventQuestion.event_id == event_name)
            .order_by(EventQuestion.idx)
            .all()
        )

    def clear_questions(self, event_name: str) -> None:
        db.session.query(EventQuestion).filter(
            EventQuestion.event_id == event_name
        ).delete(synchronize_session=False)


class EventAttemptRepository(RepositoryBase[EventAttempt]):
    """Query layer for event attempts and their snapshot children."""

    model = EventAttempt

    def find_by_name(self, name: str) -> EventAttempt | None:
        return self.find_one(name=name)

    def find_by_student_event(
        self, student_id: str, event_id: str
    ) -> EventAttempt | None:
        return (
            db.session.query(EventAttempt)
            .filter(
                EventAttempt.student_id == student_id,
                EventAttempt.event_id == event_id,
                ~EventAttempt.name.like("test-%"),
            )
            .first()
        )

    def list_by_student(self, student_id: str) -> list[EventAttempt]:
        return (
            db.session.query(EventAttempt)
            .filter(
                EventAttempt.student_id == student_id,
                ~EventAttempt.name.like("test-%"),
            )
            .all()
        )

    def delete_test_attempts(self, student_id: str, event_id: str) -> None:
        names = [
            row[0]
            for row in db.session.query(EventAttempt.name).filter(
                EventAttempt.student_id == student_id,
                EventAttempt.event_id == event_id,
                EventAttempt.name.like("test-%"),
            )
        ]
        if not names:
            return
        question_ids = [
            row[0]
            for row in db.session.query(EventAttemptQuestion.id).filter(
                EventAttemptQuestion.event_attempt_id.in_(names)
            )
        ]
        if question_ids:
            db.session.query(EventAttemptAnswer).filter(
                EventAttemptAnswer.event_attempt_question_id.in_(question_ids)
            ).delete(synchronize_session=False)
        db.session.query(EventAttemptAnswerTemp).filter(
            EventAttemptAnswerTemp.event_attempt_id.in_(names)
        ).delete(synchronize_session=False)
        db.session.query(EventAttemptQuestion).filter(
            EventAttemptQuestion.event_attempt_id.in_(names)
        ).delete(synchronize_session=False)
        db.session.query(EventAttempt).filter(
            EventAttempt.name.in_(names)
        ).delete(synchronize_session=False)

    def list_for_event(self, event_name: str) -> list[EventAttempt]:
        return (
            db.session.query(EventAttempt)
            .filter(
                EventAttempt.event_id == event_name,
                ~EventAttempt.name.like("test-%"),
            )
            .order_by(
                EventAttempt.score.desc().nullslast(),
                EventAttempt.time_limit.asc().nullslast(),
            )
            .all()
        )

    def get_attempt_questions(self, attempt_name: str) -> list[EventAttemptQuestion]:
        return (
            db.session.query(EventAttemptQuestion)
            .filter(EventAttemptQuestion.event_attempt_id == attempt_name)
            .order_by(EventAttemptQuestion.idx)
            .all()
        )

    def get_answers(self, attempt_name: str) -> list[EventAttemptAnswer]:
        return (
            db.session.query(EventAttemptAnswer)
            .join(
                EventAttemptQuestion,
                EventAttemptAnswer.event_attempt_question_id == EventAttemptQuestion.id,
            )
            .filter(EventAttemptQuestion.event_attempt_id == attempt_name)
            .all()
        )

    def get_temps(self, attempt_name: str) -> list[EventAttemptAnswerTemp]:
        return db.session.query(EventAttemptAnswerTemp).filter(
            EventAttemptAnswerTemp.event_attempt_id == attempt_name
        ).all()

    def find_temp(
        self, attempt_name: str, attempt_question_id: str
    ) -> EventAttemptAnswerTemp | None:
        return db.session.query(EventAttemptAnswerTemp).filter(
            EventAttemptAnswerTemp.event_attempt_id == attempt_name,
            EventAttemptAnswerTemp.event_attempt_question_id == attempt_question_id,
        ).first()


__all__ = ["EventAttemptRepository", "EventRepository"]
