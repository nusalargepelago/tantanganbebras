"""Topic HTTP endpoints — CRUD and ordering for chapter topics."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.infra.roles import require_staff
from app.topic.dto import TopicCreateIn, TopicReorderIn, TopicUpdateIn
from app.topic.presenters import TopicOut
from app.topic.services import TopicService
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

bp = BlueprintFactory("topic", __name__, url_prefix="/api/v1/topic")

_rate_30 = limiter.limit("30/minute")
_rate_10 = limiter.limit("10/minute")


@bp.get("")
@login_required
def list_topics():
    if denied := require_staff():
        return denied

    page = PageIn.validate(request.args)
    category = request.args.get("category") or None
    topics, total = TopicService().list_topics(
        category=category, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [TopicOut.from_topic(t).to_dict() for t in topics],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.get("/<string:name>")
@login_required
def get_topic(name: str):
    if denied := require_staff():
        return denied

    topic = TopicService().get_topic(name)
    return ok(TopicOut.from_topic(topic).to_dict())


@bp.post("")
@_rate_30
@login_required
def create_topic():
    if denied := require_staff():
        return denied

    dto = TopicCreateIn.validate(request.get_json(silent=True) or {})
    topic = TopicService().create_topic(dto, actor_id=current_user.id)
    return created(TopicOut.from_topic(topic).to_dict())


@bp.patch("/<string:name>")
@_rate_30
@login_required
def update_topic(name: str):
    if denied := require_staff():
        return denied

    dto = TopicUpdateIn.validate(request.get_json(silent=True) or {})
    topic = TopicService().update_topic(name, dto, actor_id=current_user.id)
    return ok(TopicOut.from_topic(topic).to_dict())


@bp.delete("/<string:name>")
@_rate_10
@login_required
def delete_topic(name: str):
    if denied := require_staff():
        return denied

    TopicService().delete_topic(name, actor_id=current_user.id)
    return no_content()


@bp.post("/reorder")
@_rate_30
@login_required
def reorder_topics():
    if denied := require_staff():
        return denied

    dto = TopicReorderIn.validate(request.get_json(silent=True) or {})
    count = TopicService().reorder(dto.items, actor_id=current_user.id)
    return ok({"count": count})
