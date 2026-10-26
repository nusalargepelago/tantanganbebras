"""Event models — challenge events, their questions, and student attempts.

Attempts use a **snapshot** design: ``event_attempt_questions`` copies
``question_id`` + ``idx`` at ``make`` time and is the single key-space the
client ever sees (``eventQuestionId``), so editing an event never breaks an
existing attempt (porting decision §1.2).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


class Event(db.Model):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    time_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    event_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    creator_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class EventQuestion(db.Model):
    __tablename__ = "event_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("events.name", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("questions.name", ondelete="RESTRICT"), nullable=False
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("event_id", "question_id", name="uq_event_question"),
    )


class EventAttempt(db.Model):
    __tablename__ = "event_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("events.name", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class EventAttemptQuestion(db.Model):
    __tablename__ = "event_attempt_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_attempt_id: Mapped[str] = mapped_column(
        String(140),
        ForeignKey("event_attempts.name", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("questions.name", ondelete="RESTRICT"), nullable=False
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("event_attempt_id", "question_id", name="uq_event_attempt_question"),
        Index("ix_event_attempt_questions_idx", "event_attempt_id", "idx"),
    )


class EventAttemptAnswer(db.Model):
    __tablename__ = "event_attempt_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_attempt_question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("event_attempt_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class EventAttemptAnswerTemp(db.Model):
    __tablename__ = "event_attempt_answer_temps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_attempt_id: Mapped[str] = mapped_column(
        String(140),
        ForeignKey("event_attempts.name", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_attempt_question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("event_attempt_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "event_attempt_id", "event_attempt_question_id", name="uq_event_attempt_temp"
        ),
    )


__all__ = [
    "Event",
    "EventAttempt",
    "EventAttemptAnswer",
    "EventAttemptAnswerTemp",
    "EventAttemptQuestion",
    "EventQuestion",
]
