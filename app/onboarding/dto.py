"""Onboarding input DTOs — classification form validation."""
from __future__ import annotations

from pydantic import field_validator

from app.student.dto import Category
from framework.base import DTOBase


class OnboardingStudentIn(DTOBase):
    """Validate the student classification form (email/username/password already exist)."""

    first_name: str = DTOBase.field(..., alias="firstName", min_length=1, max_length=80)
    last_name: str = DTOBase.field(..., alias="lastName", min_length=1, max_length=80)
    category: Category = DTOBase.field(...)
    school_id: str = DTOBase.field(..., alias="schoolId", min_length=1, max_length=36)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_names(cls, value):
        return value.strip() if isinstance(value, str) else value


class OnboardingTeacherIn(DTOBase):
    """Validate the teacher classification form (personal data + school)."""

    first_name: str = DTOBase.field(..., alias="firstName", min_length=1, max_length=80)
    last_name: str = DTOBase.field(..., alias="lastName", min_length=1, max_length=80)
    school_id: str = DTOBase.field(..., alias="schoolId", min_length=1, max_length=36)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_names(cls, value):
        return value.strip() if isinstance(value, str) else value


__all__ = [
    "OnboardingStudentIn",
    "OnboardingTeacherIn",
]
