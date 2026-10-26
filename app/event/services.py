"""Event services — admin CRUD and student attempt lifecycle."""
from __future__ import annotations

from datetime import UTC, datetime

from app.event.dto import EventAnswerItem, EventCreateIn, EventUpdateIn
from app.event.models import (
    Event,
    EventAttempt,
    EventAttemptAnswer,
    EventAttemptAnswerTemp,
    EventAttemptQuestion,
    EventQuestion,
)
from app.event.presenters import EventAttemptOut, EventOut
from app.event.repositories import EventAttemptRepository, EventRepository
from app.infra.audit import log as audit_log
from app.infra.naming import next_name, slugify
from app.infra.scoring import POINTS_PER_CORRECT, is_correct
from app.question.presenters import QuestionOut
from app.question.repositories import QuestionRepository
from app.student.repositories import StudentRepository
from framework.base import ServiceBase
from framework.exceptions import Conflict, Forbidden, NotFound


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class EventService(ServiceBase[EventRepository]):
    """Admin event management."""

    repository_class = EventRepository

    def __init__(
        self,
        repo: EventRepository | None = None,
        questions: QuestionRepository | None = None,
        attempts: EventAttemptRepository | None = None,
    ):
        super().__init__(repo)
        self._questions = questions or QuestionRepository()
        self._attempts = attempts or EventAttemptRepository()

    def list_events(self, **filters) -> tuple[list[dict], int]:
        events, total = self._repo.list_all(**filters)
        counts = self._repo.get_question_counts()
        return [self._serialize(e, counts.get(e.name, 0)) for e in events], total

    def get_event(self, name: str) -> dict:
        event = self._repo.find_by_name(name)
        if event is None:
            raise NotFound("event_not_found")
        rows = self._repo.get_questions(name)
        existing = {
            q.name: q for q in self._questions.find_many_by_names([r.question_id for r in rows])
        }
        out = self._serialize(event, len(rows))
        out["questions"] = [
            QuestionOut.from_question(existing[r.question_id]).to_dict()
            for r in rows
            if r.question_id in existing
        ]
        return out

    def create(self, dto: EventCreateIn, *, actor_id: str) -> dict:
        self._validate_questions(dto.questions_id, dto.category)
        name = next_name(
            slugify(dto.event_name, fallback="event"), self._repo.name_exists
        )
        event = Event(
            name=name,
            event_name=dto.event_name,
            category=dto.category,
            time_limit=dto.time_limit,
            event_deadline=dto.event_deadline,
            published=dto.published,
            description=dto.description,
            creator_id=actor_id,
        )
        self._repo.add(event)
        self._flush()
        for idx, question_id in enumerate(dto.questions_id):
            self._repo.add(EventQuestion(event_id=name, question_id=question_id, idx=idx))
        audit_log(
            "event_created",
            user_id=actor_id,
            resource=f"event/{name}",
            details={"category": dto.category, "n_questions": len(dto.questions_id)},
        )
        self._commit()
        return self._serialize(event, len(dto.questions_id))

    def update(self, name: str, dto: EventUpdateIn, *, actor_id: str) -> dict:
        event = self._repo.find_by_name(name)
        if event is None:
            raise Conflict("event_not_found")

        data = dto.model_dump(exclude_unset=True)
        question_ids = data.pop("questions_id", None)
        data = {k: v for k, v in data.items() if v is not None or k == "description"}
        changed = set(data.keys())

        if question_ids is not None:
            if not question_ids:
                raise Conflict("questions_id_required")
            self._validate_questions(question_ids, data.get("category", event.category))
            self._repo.clear_questions(name)
            for idx, question_id in enumerate(question_ids):
                self._repo.add(EventQuestion(event_id=name, question_id=question_id, idx=idx))
            changed.add("questions_id")

        for key, value in data.items():
            setattr(event, key, value)

        audit_log(
            "event_updated",
            user_id=actor_id,
            resource=f"event/{name}",
            details={"changed": sorted(changed)},
        )
        self._commit()
        return self._serialize(event, len(self._repo.get_questions(name)))

    def soft_delete(self, name: str, *, actor_id: str) -> None:
        event = self._require(name)
        event.disabled = True
        event.disabled_at = datetime.now(UTC)
        audit_log("event_soft_deleted", user_id=actor_id, resource=f"event/{name}")
        self._commit()

    def restore(self, name: str, *, actor_id: str) -> dict:
        event = self._require(name)
        event.disabled = False
        event.disabled_at = None
        audit_log("event_restored", user_id=actor_id, resource=f"event/{name}")
        self._commit()
        return self._serialize(event, len(self._repo.get_questions(name)))

    def purge(self, name: str, *, actor_id: str) -> None:
        event = self._require(name)
        self._repo.clear_questions(name)
        self._repo.delete(event)
        audit_log("event_purged", user_id=actor_id, resource=f"event/{name}")
        self._commit()

    def results(self, name: str) -> list[dict]:
        return [
            EventAttemptOut.from_attempt(a).to_dict()
            for a in self._attempts.list_for_event(name)
        ]

    def _require(self, name: str) -> Event:
        event = self._repo.find_by_name(name)
        if event is None:
            raise NotFound("event_not_found")
        return event

    def _serialize(self, event: Event, question_count: int) -> dict:
        return EventOut.from_event(event, question_count=question_count).to_dict()

    def _validate_questions(self, question_ids: list[str], category: str) -> None:
        existing = {
            q.name: q for q in self._questions.find_many_by_names(question_ids)
        }
        missing = [qid for qid in question_ids if qid not in existing]
        if missing:
            raise Conflict(f"question_not_found: {','.join(missing)}")
        for question_id in question_ids:
            question = existing[question_id]
            if question.category != category:
                raise Conflict(f"question_category_mismatch: {question_id}")
            if question.disabled:
                raise Conflict(f"question_disabled: {question_id}")


class EventAttemptService(ServiceBase[EventAttemptRepository]):
    """Student event attempts (make, start, autosave, submit, result)."""

    repository_class = EventAttemptRepository

    def __init__(
        self,
        repo: EventAttemptRepository | None = None,
        events: EventRepository | None = None,
        questions: QuestionRepository | None = None,
        students: StudentRepository | None = None,
    ):
        super().__init__(repo)
        self._events = events or EventRepository()
        self._questions = questions or QuestionRepository()
        self._students = students or StudentRepository()

    def candidates(self, student_id: str) -> dict:
        student = self._students.find_by_user_id(student_id)
        if student is None:
            return {"items": []}

        counts = self._events.get_question_counts()
        by_event = {a.event_id: a for a in self._repo.list_by_student(student_id)}
        items = []
        for event in self._events.candidates(limit=500):
            attempt = by_event.get(event.name)
            out = self._event_out(event, counts.get(event.name, 0))
            out.update(
                {
                    "categoryMatch": event.category == student.category,
                    "alreadyAttempted": attempt is not None,
                    "attemptName": attempt.name if attempt else None,
                    "attemptScore": attempt.score if attempt else None,
                    "attemptCompleted": bool(attempt and attempt.finished_at),
                }
            )
            items.append(out)
        return {"items": items}

    def make(
        self,
        student_id: str,
        event_name: str,
        *,
        test: bool = False,
        app_role: str = "user",
    ) -> dict:
        event = self._events.find_by_name(event_name)
        if event is None:
            raise Conflict("event_not_found")
        if event.disabled:
            raise Conflict("event_disabled")
        if test:
            if (
                app_role != "admin"
                and self._students.find_by_user_id(student_id) is not None
            ):
                raise Forbidden("test_requires_staff")
            self._repo.delete_test_attempts(student_id, event_name)
        else:
            if not event.published:
                raise Conflict("event_not_published")
            deadline = _as_utc(event.event_deadline)
            if deadline is not None and deadline < datetime.now(UTC):
                raise Conflict("event_expired")
            existing = self._repo.find_by_student_event(student_id, event_name)
            if existing is not None:
                return EventAttemptOut.from_attempt(existing).to_dict()

        now = datetime.now(UTC)
        prefix = "test" if test else "student"
        attempt_name = f"{prefix}-{student_id}-{event_name}-{int(now.timestamp())}"
        attempt = EventAttempt(
            name=attempt_name, student_id=student_id, event_id=event_name, started_at=now
        )
        self._repo.add(attempt)
        self._flush()
        for row in self._events.get_questions(event_name):
            self._repo.add(
                EventAttemptQuestion(
                    event_attempt_id=attempt_name,
                    question_id=row.question_id,
                    idx=row.idx,
                )
            )
        audit_log(
            "event_student_started",
            user_id=student_id,
            resource=f"event-student/{attempt_name}",
            details={"event": event_name},
        )
        self._commit()
        return EventAttemptOut.from_attempt(attempt).to_dict()

    def start(self, student_id: str, attempt_name: str) -> dict:
        attempt = self._require_owned(student_id, attempt_name)
        event = self._events.find_by_name(attempt.event_id)
        if event is None:
            raise NotFound("event_not_found")
        if event.disabled:
            raise NotFound("event_disabled")

        rows = self._repo.get_attempt_questions(attempt_name)
        resolved = self._resolve_questions(rows)
        questions = []
        for row in rows:
            question = resolved.get(row.question_id)
            if question is None:
                continue
            questions.append(
                {
                    "eventQuestionId": row.id,
                    "question": QuestionOut.from_question(question).to_dict(),
                }
            )
        saved = [
            {"eventQuestionId": t.event_attempt_question_id, "answer": t.answer}
            for t in self._repo.get_temps(attempt_name)
        ]
        return {
            "event": self._event_out(event, len(rows)),
            "eventStudent": EventAttemptOut.from_attempt(attempt).to_dict(),
            "questions": questions,
            "savedAnswers": saved,
        }

    def save_temp(
        self, student_id: str, attempt_name: str, event_question_id: str, answer: str | None
    ) -> dict:
        attempt = self._require_owned(student_id, attempt_name)
        if attempt.finished_at is not None:
            raise NotFound("attempt_already_submitted")
        event = self._events.find_by_name(attempt.event_id)
        if event is not None and event.disabled:
            raise NotFound("event_disabled")

        temp = self._repo.find_temp(attempt_name, event_question_id)
        if temp is not None:
            temp.answer = answer or ""
        else:
            self._repo.add(
                EventAttemptAnswerTemp(
                    event_attempt_id=attempt_name,
                    event_attempt_question_id=event_question_id,
                    answer=answer or "",
                )
            )
        self._commit()
        return {"notEmpty": bool(answer and answer.strip())}

    def submit(
        self, student_id: str, attempt_name: str, answers: list[EventAnswerItem]
    ) -> dict:
        attempt = self._require_owned(student_id, attempt_name)
        if attempt.finished_at is not None:
            raise Conflict("attempt_already_submitted")
        event = self._events.find_by_name(attempt.event_id)
        if event is not None and event.disabled:
            raise Conflict("event_disabled")

        answer_map = {a.event_question_id: a.answer for a in answers}
        rows = self._repo.get_attempt_questions(attempt_name)
        resolved = self._resolve_questions(rows)
        score = 0
        for row in rows:
            question = resolved.get(row.question_id)
            if question is None:
                continue
            response = answer_map.get(row.id)
            correct = is_correct(question, response)
            self._repo.add(
                EventAttemptAnswer(
                    event_attempt_question_id=row.id,
                    answer=response or "",
                    is_correct=correct,
                )
            )
            if correct:
                score += POINTS_PER_CORRECT

        now = datetime.now(UTC)
        attempt.score = score
        attempt.finished_at = now
        started = _as_utc(attempt.started_at)
        if started is not None:
            attempt.time_limit = int((now - started).total_seconds())

        audit_log(
            "event_student_submitted",
            user_id=student_id,
            resource=f"event-student/{attempt_name}",
            details={"score": score},
        )
        self._commit()
        return EventAttemptOut.from_attempt(attempt).to_dict()

    def result(self, student_id: str, attempt_name: str) -> dict:
        attempt = self._require_owned(student_id, attempt_name)
        return EventAttemptOut.from_attempt(attempt).to_dict()

    def _require_owned(self, student_id: str, attempt_name: str) -> EventAttempt:
        attempt = self._repo.find_by_name(attempt_name)
        if attempt is None or attempt.student_id != student_id:
            raise NotFound("attempt_not_found")
        return attempt

    def _resolve_questions(self, rows) -> dict:
        names = [r.question_id for r in rows]
        return {q.name: q for q in self._questions.find_many_by_names(names)}

    def _event_out(self, event: Event, question_count: int) -> dict:
        return EventOut.from_event(event, question_count=question_count).to_dict()


__all__ = ["EventAttemptService", "EventService"]
