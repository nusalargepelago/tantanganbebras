"""Onboarding services — post-register role classification (student or teacher)."""
from __future__ import annotations

from app.auth.models import TEACHER_ROLE
from app.auth.repositories import RoleRepository
from app.infra.audit import log as audit_log
from app.onboarding.dto import OnboardingStudentIn, OnboardingTeacherIn
from app.onboarding.models import Teacher
from app.onboarding.repositories import TeacherRepository
from app.school.services import SchoolService
from app.student.models import Student
from app.student.repositories import StudentRepository
from framework.base import ServiceBase
from framework.exceptions import Conflict, Forbidden


class OnboardingService(ServiceBase[Teacher]):
    repository_class = TeacherRepository

    def __init__(
        self,
        repo: TeacherRepository | None = None,
        students: StudentRepository | None = None,
        roles: RoleRepository | None = None,
        schools: SchoolService | None = None,
    ):
        super().__init__(repo)
        self._students = students or StudentRepository()
        self._roles = roles or RoleRepository()
        self._schools = schools or SchoolService()

    # --- classification ---------------------------------------------------

    def classification_of(self, user_id: str) -> str:
        if self._students.find_by_user_id(user_id) is not None:
            return "student"
        return "teacher" if self._repo.find_by_user_id(user_id) is not None else "none"

    def status(self, user) -> dict:
        return {"classification": self.classification_of(str(user.id))}

    def classify_student(self, user, dto: OnboardingStudentIn, *, actor_id: str) -> dict:
        self._ensure_classifiable(user)
        self._apply_names(user, dto.first_name, dto.last_name)
        self._schools.require_school(dto.school_id)
        student = Student(
            user_id=user.id,
            category=dto.category,
            school_id=dto.school_id,
            status="Inactive",
            disabled=False,
        )
        self._students.add(student)
        self._flush()
        audit_log(
            "onboarding_classify_student",
            user_id=actor_id,
            resource="onboarding/student",
            details={"category": dto.category, "schoolId": dto.school_id},
        )
        self._commit()
        return {"classification": "student"}

    def classify_teacher(self, user, dto: OnboardingTeacherIn, *, actor_id: str) -> dict:
        self._ensure_classifiable(user)
        self._apply_names(user, dto.first_name, dto.last_name)
        self._schools.require_school(dto.school_id)
        teacher = Teacher(
            user_id=user.id,
            school_id=dto.school_id,
        )
        self._repo.add(teacher)
        self._assign_teacher_role(user)
        self._flush()
        audit_log(
            "onboarding_classify_teacher",
            user_id=actor_id,
            resource="onboarding/teacher",
            details={"schoolId": dto.school_id},
        )
        self._commit()
        return {"classification": "teacher"}

    # --- internals ---------------------------------------------------------

    def _ensure_classifiable(self, user) -> None:
        if getattr(user, "app_role", None) == "admin":
            raise Forbidden("classification_not_applicable")
        if self._students.find_by_user_id(user.id) is not None:
            raise Conflict("classification_already_set")
        if self._repo.find_by_user_id(user.id) is not None:
            raise Conflict("classification_already_set")
        if any(role.name == TEACHER_ROLE for role in getattr(user, "roles", [])):
            raise Conflict("classification_already_set")

    def _apply_names(self, user, first_name: str, last_name: str) -> None:
        user.first_name = first_name
        user.last_name = last_name
        user.full_name = f"{first_name} {last_name}".strip()

    def _assign_teacher_role(self, user) -> None:
        role = self._roles.find_by_name(TEACHER_ROLE)
        if role is None:
            from app.auth.models import Role

            role = Role(name=TEACHER_ROLE)
            self._roles.add(role)
            self._flush()
        user.roles.append(role)


__all__ = ["OnboardingService"]
