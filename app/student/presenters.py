"""Student presenters — wire serialization for students and student-auth."""
from __future__ import annotations

from app.auth.models import User
from app.infra.presenters import UtcPresenterBase
from app.student.models import Student
from framework.base import PresenterBase


class StudentOut(UtcPresenterBase):
    """Student on the wire (joined with its User for identity fields)."""

    user_id: str = PresenterBase.field(alias="userId")
    username: str
    email: str
    first_name: str = PresenterBase.field(alias="firstName")
    last_name: str = PresenterBase.field(alias="lastName")
    category: str
    school: str | None = PresenterBase.field(None)
    city: str | None = PresenterBase.field(None)
    country: str | None = PresenterBase.field(None)
    status: str
    disabled: bool = PresenterBase.field(False)
    disabled_at: str | None = PresenterBase.field(None, alias="disabledAt")
    created_at: str | None = PresenterBase.field(None, alias="createdAt")

    @classmethod
    def from_student(cls, student: Student, user: User) -> StudentOut:
        return cls.from_model(
            student,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )


class StudentUserOut(PresenterBase):
    """Compact user payload for the student-auth session."""

    id: str
    username: str
    email: str
    first_name: str = PresenterBase.field(alias="firstName")
    last_name: str = PresenterBase.field(alias="lastName")
    is_active: bool = PresenterBase.field(True, alias="isActive")

    @classmethod
    def from_user(cls, user: User) -> StudentUserOut:
        return cls.from_model(user)


__all__ = ["StudentOut", "StudentUserOut"]
