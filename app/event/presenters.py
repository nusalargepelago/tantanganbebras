"""Event presenters — wire serialization for events and attempts."""
from __future__ import annotations

from app.event.models import Event, EventAttempt
from app.infra.presenters import UtcPresenterBase
from framework.base import PresenterBase


class EventOut(UtcPresenterBase):
    """Event on the wire (with aggregated question count)."""

    name: str
    event_name: str = PresenterBase.field(alias="eventName")
    category: str
    time_limit: int = PresenterBase.field(60, alias="timeLimit")
    event_deadline: str = PresenterBase.field(alias="eventDeadline")
    published: bool = PresenterBase.field(False)
    description: str | None = PresenterBase.field(None)
    disabled: bool = PresenterBase.field(False)
    disabled_at: str | None = PresenterBase.field(None, alias="disabledAt")
    created_at: str | None = PresenterBase.field(None, alias="createdAt")
    updated_at: str | None = PresenterBase.field(None, alias="updatedAt")
    question_count: int = PresenterBase.field(0, alias="questionCount")

    @classmethod
    def from_event(cls, event: Event, *, question_count: int = 0) -> EventOut:
        return cls.from_model(event, question_count=question_count)


class EventAttemptOut(UtcPresenterBase):
    """One student event attempt on the wire."""

    name: str
    student_id: str = PresenterBase.field(alias="studentId")
    event_id: str = PresenterBase.field(alias="eventId")
    score: int | None = PresenterBase.field(None)
    time_limit: int | None = PresenterBase.field(None, alias="timeLimit")
    started_at: str | None = PresenterBase.field(None, alias="startedAt")
    finished_at: str | None = PresenterBase.field(None, alias="finishedAt")
    created_at: str | None = PresenterBase.field(None, alias="createdAt")
    updated_at: str | None = PresenterBase.field(None, alias="updatedAt")

    @classmethod
    def from_attempt(cls, attempt: EventAttempt) -> EventAttemptOut:
        return cls.from_model(attempt)


__all__ = ["EventAttemptOut", "EventOut"]
