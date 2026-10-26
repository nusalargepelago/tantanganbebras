"""Question HTTP endpoints — the question bank."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.infra.enums import (
    CATEGORIES,
    DIFFICULTY_LEVELS,
    OPTION_LETTERS,
    QUESTION_TYPES,
    STATUSES,
)
from app.infra.roles import require_staff
from app.question.dto import QuestionCreateIn, QuestionUpdateIn
from app.question.presenters import QuestionOut
from app.question.services import QuestionService
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

bp = BlueprintFactory("question", __name__, url_prefix="/api/v1/question")

_rate_30 = limiter.limit("30/minute")
_rate_10 = limiter.limit("10/minute")
_rate_5 = limiter.limit("5/minute")


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@bp.get("")
@login_required
def list_questions():
    if denied := require_staff():
        return denied

    page = PageIn.validate(request.args)
    args = request.args
    questions, total = QuestionService().list_questions(
        category=args.get("category") or None,
        status=args.get("status") or None,
        difficulty_level=(
            args.get("difficultyLevel") or args.get("difficulty_level") or None
        ),
        topic_id=(args.get("topicId") or args.get("topic") or None),
        q=(args.get("q") or "").strip() or None,
        include_disabled=_truthy(
            args.get("includeDisabled") or args.get("include_disabled")
        ),
        page=page.page,
        per_page=page.per_page,
    )
    return paginated_response(
        paginate(
            [QuestionOut.list_row(q) for q in questions],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.get("/option-list")
@login_required
def option_list():
    if denied := require_staff():
        return denied

    return ok(
        {
            "category": list(CATEGORIES),
            "difficultyLevel": list(DIFFICULTY_LEVELS),
            "questionType": list(QUESTION_TYPES),
            "option": list(OPTION_LETTERS),
            "status": list(STATUSES),
        }
    )


@bp.get("/<string:name>")
@login_required
def get_question(name: str):
    if denied := require_staff():
        return denied

    question = QuestionService().get_question(name)
    return ok(QuestionOut.from_question(question).to_dict())


@bp.post("")
@_rate_30
@login_required
def create_question():
    if denied := require_staff():
        return denied

    dto = QuestionCreateIn.validate(request.get_json(silent=True) or {})
    question = QuestionService().create_question(dto, actor_id=current_user.id)
    return created(QuestionOut.from_question(question).to_dict())


@bp.patch("/<string:name>")
@_rate_30
@login_required
def update_question(name: str):
    if denied := require_staff():
        return denied

    dto = QuestionUpdateIn.validate(request.get_json(silent=True) or {})
    question = QuestionService().update_question(name, dto, actor_id=current_user.id)
    return ok(QuestionOut.from_question(question).to_dict())


@bp.delete("/<string:name>")
@_rate_10
@login_required
def soft_delete_question(name: str):
    if denied := require_staff():
        return denied

    QuestionService().soft_delete(name, actor_id=current_user.id)
    return no_content()


@bp.post("/<string:name>/restore")
@_rate_10
@login_required
def restore_question(name: str):
    if denied := require_staff():
        return denied

    QuestionService().restore(name, actor_id=current_user.id)
    return ok({"message": "restored"})


@bp.delete("/<string:name>/purge")
@_rate_5
@login_required
def purge_question(name: str):
    if denied := require_staff():
        return denied

    QuestionService().purge(name, actor_id=current_user.id)
    return no_content()
