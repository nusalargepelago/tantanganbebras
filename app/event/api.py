"""Event HTTP endpoints — admin challenge management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.event.dto import EventCreateIn, EventUpdateIn
from app.event.services import EventService
from app.infra.roles import require_staff
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

bp = BlueprintFactory("event", __name__, url_prefix="/api/v1/event")

_rate_20 = limiter.limit("20/minute")
_rate_10 = limiter.limit("10/minute")
_rate_5 = limiter.limit("5/minute")


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@bp.get("")
@login_required
def list_events():
    if denied := require_staff():
        return denied

    page = PageIn.validate(request.args)
    args = request.args
    published_raw = args.get("published")
    items, total = EventService().list_events(
        category=args.get("category") or None,
        published=None if published_raw is None else published_raw.lower() == "true",
        include_disabled=_truthy(
            args.get("includeDisabled") or args.get("include_disabled")
        ),
        page=page.page,
        per_page=page.per_page,
    )
    return paginated_response(paginate(items, total, page.page, page.per_page))


@bp.post("")
@_rate_20
@login_required
def create_event():
    if denied := require_staff():
        return denied

    dto = EventCreateIn.validate(request.get_json(silent=True) or {})
    event = EventService().create(dto, actor_id=current_user.id)
    return created(event)


@bp.get("/<string:name>")
@login_required
def get_event(name: str):
    if denied := require_staff():
        return denied

    return ok(EventService().get_event(name))


@bp.patch("/<string:name>")
@_rate_20
@login_required
def update_event(name: str):
    if denied := require_staff():
        return denied

    dto = EventUpdateIn.validate(request.get_json(silent=True) or {})
    return ok(EventService().update(name, dto, actor_id=current_user.id))


@bp.delete("/<string:name>")
@_rate_10
@login_required
def soft_delete_event(name: str):
    if denied := require_staff():
        return denied

    EventService().soft_delete(name, actor_id=current_user.id)
    return no_content()


@bp.post("/<string:name>/restore")
@_rate_10
@login_required
def restore_event(name: str):
    if denied := require_staff():
        return denied

    return ok(EventService().restore(name, actor_id=current_user.id))


@bp.delete("/<string:name>/purge")
@_rate_5
@login_required
def purge_event(name: str):
    if denied := require_staff():
        return denied

    EventService().purge(name, actor_id=current_user.id)
    return no_content()


@bp.get("/<string:name>/results")
@login_required
def event_results(name: str):
    if denied := require_staff():
        return denied

    items = EventService().results(name)
    return ok({"items": items})
