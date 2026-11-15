"""Onboarding repositories — persistence only, no commit boundary."""
from __future__ import annotations

from app.onboarding.models import Teacher
from framework.base import RepositoryBase


class TeacherRepository(RepositoryBase[Teacher]):
    model = Teacher

    def find_by_user_id(self, user_id: str) -> Teacher | None:
        return self.find_one(user_id=user_id)


__all__ = ["TeacherRepository"]
