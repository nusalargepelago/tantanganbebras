"""Role seeding and staff gate — ensures builtin roles exist."""
from __future__ import annotations

from flask_login import current_user

from app.auth.models import MEMBER_ROLE, TEACHER_ROLE, Role
from framework.api.response import error
from framework.extensions import db


def _roles_table_exists() -> bool:
    from sqlalchemy import inspect

    try:
        return "roles" in inspect(db.engine).get_table_names()
    except Exception:
        return False


def ensure_builtin_roles() -> None:
    """Seed the builtin roles. Idempotent; runs after migrations on boot."""
    if not _roles_table_exists():
        return

    existing = {r.name for r in db.session.query(Role).all()}
    for name in (MEMBER_ROLE, TEACHER_ROLE):
        if name not in existing:
            db.session.add(Role(name=name))
            db.session.commit()


def _has_row(table: str, user_id: str) -> bool:
    if table not in db.metadata.tables:
        return False
    if table == "students":
        from app.student.models import Student

        return db.session.get(Student, user_id) is not None
    if table == "teachers":
        from app.onboarding.models import Teacher

        return db.session.get(Teacher, user_id) is not None
    return False


def _teacher_row(user_id: str):
    """Return the teacher row for ``user_id``, or None."""
    if "teachers" not in db.metadata.tables:
        return None
    from app.onboarding.models import Teacher

    return db.session.get(Teacher, user_id)


def teacher_school_id(user_id: str) -> str | None:
    """Return the school_id of the teacher row for ``user_id``, or None."""
    teacher = _teacher_row(user_id)
    return teacher.school_id if teacher is not None else None


def require_staff():
    """Return a 401/403 response unless the caller is staff.

    Staff = ``app_role == "admin"`` or an account without a student or teacher
    discriminator row. Students and teachers are blocked from staff-only
    Tantangan Bebras domains. Returns ``None`` when the caller may proceed.
    """
    if not current_user.is_authenticated:
        return error("unauthorized", 401)
    if getattr(current_user, "app_role", None) == "admin":
        return None
    user_id = str(current_user.get_id())
    if _has_row("students", user_id) or _has_row("teachers", user_id):
        return error("forbidden", 403)
    return None


def require_student_manager():
    """Return a 401/403 response unless the caller may manage students.

    Admin and staff (accounts without a student or teacher discriminator
    row) keep the behavior of ``require_staff()``. Additionally, teachers
    — ``has_role('Teacher')`` — may manage students, but only scoped to
    their own school. Students are never allowed. Teachers without a
    ``teachers`` row are rejected with ``teacher_school_missing``.
    Returns ``None`` when the caller may proceed. Use
    ``student_manager_scope()`` to get the school scope to apply.
    """
    if not current_user.is_authenticated:
        return error("unauthorized", 401)
    if getattr(current_user, "app_role", None) == "admin":
        return None
    user_id = str(current_user.get_id())
    if _has_row("students", user_id):
        return error("forbidden", 403)
    if hasattr(current_user, "has_role") and current_user.has_role(TEACHER_ROLE):
        if teacher_school_id(user_id) is None:
            return error("teacher_school_missing", 403)
        return None
    if _has_row("teachers", user_id):
        # teachers row without the Teacher role — inconsistent state; deny.
        return error("forbidden", 403)
    return None


def student_manager_scope() -> str | None:
    """Return the school scope for the current student manager.

    ``None`` means unscoped (admin or regular staff) — the caller sees
    everything. A teacher's caller sees only students in this school.
    Contract: call ``require_student_manager()`` first and only when it
    returns ``None``; call sites that skip the gate are misuses.
    """
    if not current_user.is_authenticated:
        return None
    if getattr(current_user, "app_role", None) == "admin":
        return None
    user_id = str(current_user.get_id())
    if hasattr(current_user, "has_role") and current_user.has_role(TEACHER_ROLE):
        return teacher_school_id(user_id)
    return None


__all__ = [
    "MEMBER_ROLE",
    "TEACHER_ROLE",
    "ensure_builtin_roles",
    "require_staff",
    "require_student_manager",
    "student_manager_scope",
    "teacher_school_id",
]
