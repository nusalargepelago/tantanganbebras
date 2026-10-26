"""Role seeding and staff gate — ensures the Member role exists."""
from __future__ import annotations

from flask_login import current_user

from app.auth.models import MEMBER_ROLE, Role
from framework.api.response import error
from framework.extensions import db


def _roles_table_exists() -> bool:
    from sqlalchemy import inspect

    try:
        return "roles" in inspect(db.engine).get_table_names()
    except Exception:
        return False


def ensure_member_role() -> None:
    """Seed the Member role. Idempotent; runs after migrations on boot."""
    if not _roles_table_exists():
        return

    existing = {r.name for r in db.session.query(Role).all()}
    if MEMBER_ROLE not in existing:
        db.session.add(Role(name=MEMBER_ROLE))
        db.session.commit()


def _is_student(user_id: str) -> bool:
    if "students" not in db.metadata.tables:
        return False
    from app.student.models import Student

    return db.session.get(Student, user_id) is not None


def require_staff():
    """Return a 401/403 response unless the caller is staff.

    Staff = ``app_role == "admin"`` or an account without a student
    discriminator row. Students are blocked from staff-only Tantangan Bebras domains.
    Returns ``None`` when the caller may proceed.
    """
    if not current_user.is_authenticated:
        return error("unauthorized", 401)
    if getattr(current_user, "app_role", None) == "admin":
        return None
    if _is_student(str(current_user.get_id())):
        return error("forbidden", 403)
    return None


__all__ = [
    "MEMBER_ROLE",
    "Role",
    "ensure_member_role",
    "require_staff",
]
