"""Student domain — re-exports blueprints, services, model, DTOs, and presenters."""
from __future__ import annotations

from app.student.api import bp
from app.student.api_auth import bp as student_auth_bp
from app.student.api_dashboard import bp as student_dashboard_bp
from app.student.api_import import bp as student_import_bp
from app.student.dto import StudentCreateIn, StudentRegisterIn, StudentUpdateIn
from app.student.models import Student
from app.student.presenters import StudentOut
from app.student.services import StudentAuthService, StudentService

__all__ = [
    "Student",
    "StudentAuthService",
    "StudentCreateIn",
    "StudentOut",
    "StudentRegisterIn",
    "StudentService",
    "StudentUpdateIn",
    "bp",
    "student_auth_bp",
    "student_dashboard_bp",
    "student_import_bp",
]
