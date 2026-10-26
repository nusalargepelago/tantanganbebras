"""Student event HTTP endpoints — candidates, runner, autosave, submit, result."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.event.dto import EventAnswerTempIn, EventSubmitIn
from app.event.services import EventAttemptService
from framework.api import BlueprintFactory, created, ok
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("event_student", __name__, url_prefix="/api/v1/student/event")

_rate_120 = limiter.limit("120/minute")
_rate_10 = limiter.limit("10/minute")


@bp.get("")
@login_required
def candidates():
    return ok(EventAttemptService().candidates(current_user.id))


@bp.post("/make/<string:event_name>")
@_rate_10
@login_required
def make_attempt(event_name: str):
    attempt = EventAttemptService().make(
        current_user.id,
        event_name,
        test=request.args.get("test") == "1",
        app_role=current_user.app_role or "user",
    )
    return created(attempt)


@bp.get("/start/<string:attempt_name>")
@login_required
def start_attempt(attempt_name: str):
    return ok(EventAttemptService().start(current_user.id, attempt_name))


@bp.post("/answer-temp")
@_rate_120
@login_required
def save_answer_temp():
    dto = EventAnswerTempIn.validate(request.get_json(silent=True) or {})
    result = EventAttemptService().save_temp(
        current_user.id, dto.event_student_name, dto.event_question_id, dto.answer
    )
    return ok(result)


@bp.post("/store")
@_rate_10
@login_required
def submit_attempt():
    dto = EventSubmitIn.validate(request.get_json(silent=True) or {})
    result = EventAttemptService().submit(
        current_user.id, dto.event_student_name, dto.answers
    )
    return ok(result)


@bp.get("/<string:attempt_name>")
@login_required
def attempt_result(attempt_name: str):
    return ok(EventAttemptService().result(current_user.id, attempt_name))
