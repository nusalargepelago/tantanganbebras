"""Question model — the question bank (MC / Essay)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


class Question(db.Model):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    question_code: Mapped[str] = mapped_column(
        String(40), nullable=False, default="Mini Challenge"
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Multiple Choice"
    )
    option_a: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_b: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_c: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_d: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(String(8), nullable=True)
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    difficulty_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Easy"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Active")
    creator_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[str | None] = mapped_column(
        String(140), ForeignKey("topics.name", ondelete="SET NULL"), nullable=True, index=True
    )
    disabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    disabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_questions_category_status", "category", "status"),
        Index("ix_questions_category_difficulty_level", "category", "difficulty_level"),
    )


__all__ = ["Question"]
