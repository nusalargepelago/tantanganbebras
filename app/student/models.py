"""Student model — the discriminator row above User for Tantangan Bebras students."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.models import User
from app.school.models import School
from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


class Student(db.Model):
    __tablename__ = "students"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="cub")
    school_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schools.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Inactive", index=True)
    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_id], lazy="joined")
    school: Mapped[School] = relationship("School", lazy="joined")

    __table_args__ = (Index("ix_students_category_status", "category", "status"),)


__all__ = ["Student"]
