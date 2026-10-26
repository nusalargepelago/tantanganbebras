"""Student HTTP endpoints — admin management of student accounts."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.infra.roles import require_staff
from app.student.dto import StudentCreateIn, StudentUpdateIn
from app.student.presenters import StudentOut
from app.student.services import StudentService
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    no_content,
    ok,
    paginate,
    paginated_response,
)
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("student", __name__, url_prefix="/api/v1/student")

_rate_20 = limiter.limit("20/minute")
_rate_10 = limiter.limit("10/minute")
_rate_5 = limiter.limit("5/minute")
_rate_30 = limiter.limit("30/minute")


def _serialize(user, student) -> dict:
    return StudentOut.from_student(student, user).to_dict()


@bp.get("")
@login_required
def list_students():
    if denied := require_staff():
        return denied

    page = PageIn.validate(request.args)
    args = request.args
    students, total = StudentService().list_students(
        category=args.get("category") or None,
        status=args.get("status") or None,
        q=(args.get("q") or "").strip() or None,
        include_disabled=(args.get("includeDisabled") or "").strip().lower()
        in {"1", "true", "yes", "on"},
        page=page.page,
        per_page=page.per_page,
    )
    return paginated_response(
        paginate(
            [_serialize(s.user, s) for s in students],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.get("/<string:user_id>")
@login_required
def get_student(user_id: str):
    if denied := require_staff():
        return denied

    user, student = StudentService().get_student(user_id)
    return ok(_serialize(user, student))


@bp.post("")
@_rate_20
@login_required
def create_student():
    if denied := require_staff():
        return denied

    dto = StudentCreateIn.validate(request.get_json(silent=True) or {})
    student = StudentService().create_student(dto, actor_id=current_user.id)
    return created(_serialize(student.user, student))


@bp.patch("/<string:user_id>")
@_rate_20
@login_required
def update_student(user_id: str):
    if denied := require_staff():
        return denied

    dto = StudentUpdateIn.validate(request.get_json(silent=True) or {})
    user, student = StudentService().update_student(user_id, dto, actor_id=current_user.id)
    return ok(_serialize(user, student))


@bp.delete("/<string:user_id>")
@_rate_10
@login_required
def soft_delete_student(user_id: str):
    if denied := require_staff():
        return denied

    StudentService().soft_delete(user_id, actor_id=current_user.id)
    return no_content()


@bp.post("/<string:user_id>/restore")
@_rate_10
@login_required
def restore_student(user_id: str):
    if denied := require_staff():
        return denied

    user, student = StudentService().restore(user_id, actor_id=current_user.id)
    return ok(_serialize(user, student))


@bp.post("/<string:user_id>/activate")
@_rate_30
@login_required
def activate_student(user_id: str):
    if denied := require_staff():
        return denied

    user, student = StudentService().activate(user_id, actor_id=current_user.id)
    return ok(_serialize(user, student))


@bp.delete("/<string:user_id>/purge")
@_rate_5
@login_required
def purge_student(user_id: str):
    if denied := require_staff():
        return denied

    StudentService().purge(user_id, actor_id=current_user.id)
    return no_content()
