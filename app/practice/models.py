"""Practice models — a student's 10-question practice sheet and its children."""
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


class Practice(db.Model):
    __tablename__ = "practices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="cub", index=True)
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


class PracticeQuestion(db.Model):
    __tablename__ = "practice_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    practice_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("practices.name", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("questions.name", ondelete="RESTRICT"), nullable=False
    )
    shuffled_idx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("practice_id", "question_id", name="uq_practice_question"),
        Index("ix_practice_questions_shuffled", "practice_id", "shuffled_idx"),
    )


class PracticeBeforeShuffle(db.Model):
    __tablename__ = "practice_before_shuffle"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    practice_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("practices.name", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("questions.name", ondelete="RESTRICT"), nullable=False
    )
    original_idx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PracticeAnswer(db.Model):
    __tablename__ = "practice_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    practice_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("practices.name", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("questions.name", ondelete="RESTRICT"), nullable=False
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("practice_id", "question_id", name="uq_practice_answer"),
    )


class PracticeAnswerTemp(db.Model):
    __tablename__ = "practice_answer_temps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    practice_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("practices.name", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(140), ForeignKey("questions.name", ondelete="RESTRICT"), nullable=False
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("practice_id", "question_id", name="uq_practice_answer_temp"),
    )


__all__ = [
    "Practice",
    "PracticeAnswer",
    "PracticeAnswerTemp",
    "PracticeBeforeShuffle",
    "PracticeQuestion",
]
