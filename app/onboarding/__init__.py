"""Onboarding domain — public surface."""
from __future__ import annotations

from app.onboarding.api import bp
from app.onboarding.dto import OnboardingStudentIn, OnboardingTeacherIn
from app.onboarding.models import Teacher
from app.onboarding.repositories import TeacherRepository
from app.onboarding.services import OnboardingService

__all__ = [
    "OnboardingService",
    "OnboardingStudentIn",
    "OnboardingTeacherIn",
    "Teacher",
    "TeacherRepository",
    "bp",
]
