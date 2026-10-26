"""Student-auth HTTP endpoints — public self-registration and login."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required, login_user, logout_user

from app.infra.csrf import clear_session_keep_csrf
from app.student.dto import StudentLoginIn, StudentRegisterIn
from app.student.presenters import StudentOut, StudentUserOut
from app.student.services import StudentAuthService, branding
from framework.api import BlueprintFactory, created, error, ok
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("student_auth", __name__, url_prefix="/api/v1/student/auth")

_rate_5 = limiter.limit("5/minute")
_rate_10 = limiter.limit("10/minute")


def _session_payload(user, student) -> dict:
    return {
        "user": StudentUserOut.from_user(user).to_dict(),
        "student": StudentOut.from_student(student, user).to_dict() if student else None,
    }


@bp.get("/login")
def student_branding():
    return ok(branding())


@bp.post("/register")
@_rate_5
def student_register():
    dto = StudentRegisterIn.validate(request.get_json(silent=True) or {})
    user, student = StudentAuthService().register(dto)

    clear_session_keep_csrf()
    login_user(user, remember=True)
    return created(_session_payload(user, student))


@bp.post("/login")
@_rate_10
def student_login():
    dto = StudentLoginIn.validate(request.get_json(silent=True) or {})
    result = StudentAuthService().authenticate(dto)
    if result is None:
        return error("invalid_credentials", 401)

    user, student = result
    clear_session_keep_csrf()
    login_user(user, remember=True)
    return ok(_session_payload(user, student))


@bp.post("/logout")
@_rate_10
@login_required
def student_logout():
    user_id = current_user.get_id()
    logout_user()
    StudentAuthService().record_logout(user_id)
    return ok({"message": "logged_out"})


@bp.get("/me")
@login_required
def student_me():
    user, student = StudentAuthService().get_me(current_user.get_id())
    return ok(_session_payload(user, student))
