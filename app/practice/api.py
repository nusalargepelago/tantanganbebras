"""Practice HTTP endpoints — student practice sheets and admin review."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.infra.roles import require_staff
from app.practice.dto import AnswerTempIn, CreateIn, PracticeSettingsIn, SubmitIn
from app.practice.services import PracticeService
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    error,
    ok,
    paginate,
    paginated_response,
)
from framework.auth import require_role
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("practice", __name__, url_prefix="/api/v1/student/practice")
staff_bp = BlueprintFactory("practice_staff", __name__, url_prefix="/api/v1/practice")

_rate_10 = limiter.limit("10/minute")
_rate_120 = limiter.limit("120/minute")


@bp.post("/create")
@_rate_10
@login_required
def create_practice():
    dto = CreateIn.validate(request.args)
    return created(
        PracticeService().create(
            current_user.id,
            test=dto.test,
            category=dto.category,
            app_role=current_user.app_role or "user",
        )
    )


@bp.get("/start")
@login_required
def start_practice():
    result = PracticeService().start(current_user.id)
    if result is None:
        return error("no_active_practice", 404)
    return ok(result)


@bp.post("/answer-temp")
@_rate_120
@login_required
def save_answer_temp():
    dto = AnswerTempIn.validate(request.get_json(silent=True) or {})
    result = PracticeService().save_temp(
        current_user.id, dto.practice_name, dto.question_id, dto.answer
    )
    return ok(result)


@bp.post("/store")
@_rate_10
@login_required
def submit_practice():
    dto = SubmitIn.validate(request.get_json(silent=True) or {})
    result = PracticeService().submit(current_user.id, dto.practice_name, dto.answers)
    return ok(result)


@bp.get("/mine")
@login_required
def my_practices():
    items = PracticeService().mine(current_user.id)
    return ok({"items": items})


@staff_bp.get("/<string:name>")
@login_required
def admin_detail(name: str):
    if denied := require_staff():
        return denied
    return ok(PracticeService().admin_detail(name))


@staff_bp.get("")
@login_required
def list_practices():
    if denied := require_staff():
        return denied

    page = PageIn.validate(request.args)
    args = request.args
    items, total = PracticeService().list_admin(
        category=args.get("category") or None,
        student_id=(args.get("studentId") or args.get("student_id") or None),
        page=page.page,
        per_page=page.per_page,
    )
    return paginated_response(paginate(items, total, page.page, page.per_page))


@staff_bp.get("/settings")
@login_required
def get_practice_settings():
    if denied := require_staff():
        return denied
    return ok({"minQuestions": PracticeService().min_questions()})


@staff_bp.put("/settings")
@login_required
def set_practice_settings():
    if denied := require_role("admin"):
        return denied
    dto = PracticeSettingsIn.validate(request.get_json(silent=True) or {})
    value = PracticeService().update_min_questions(
        dto.min_questions, changed_by=current_user.id
    )
    return ok({"minQuestions": value})


@bp.get("/<string:name>")
@login_required
def practice_detail(name: str):
    return ok(PracticeService().detail(current_user.id, name))
