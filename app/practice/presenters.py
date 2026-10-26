"""Practice presenters — wire serialization for practice sheets."""
from __future__ import annotations

from app.infra.presenters import UtcPresenterBase
from app.practice.models import Practice
from framework.base import PresenterBase


class PracticeOut(UtcPresenterBase):
    """Practice sheet on the wire."""

    name: str
    student_id: str = PresenterBase.field(alias="studentId")
    category: str
    score: int | None = PresenterBase.field(None)
    time_limit: int | None = PresenterBase.field(None, alias="timeLimit")
    started_at: str | None = PresenterBase.field(None, alias="startedAt")
    finished_at: str | None = PresenterBase.field(None, alias="finishedAt")
    created_at: str | None = PresenterBase.field(None, alias="createdAt")
    updated_at: str | None = PresenterBase.field(None, alias="updatedAt")

    @classmethod
    def from_practice(cls, practice: Practice) -> PracticeOut:
        return cls.from_model(practice)


class PracticeAdminOut(PracticeOut):
    """Admin review row — practice sheet with its student's name, email, school."""

    student_name: str | None = PresenterBase.field(None, alias="studentName")
    student_email: str | None = PresenterBase.field(None, alias="studentEmail")
    student_school: str | None = PresenterBase.field(None, alias="studentSchool")

    @classmethod
    def from_practice(
        cls,
        practice: Practice,
        *,
        student_name: str | None = None,
        student_email: str | None = None,
        student_school: str | None = None,
    ) -> PracticeAdminOut:
        return cls.from_model(
            practice,
            student_name=student_name,
            student_email=student_email,
            student_school=student_school,
        )


__all__ = ["PracticeAdminOut", "PracticeOut"]
