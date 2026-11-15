"""Master data API — session-readable cities/schools, admin school CRUD."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.school.dto import SchoolCreateIn, SchoolUpdateIn
from app.school.presenters import CityOut, SchoolOut
from app.school.services import CityService, SchoolService
from framework.api import BlueprintFactory, created, ok
from framework.auth.helpers import require_role

bp = BlueprintFactory("school", __name__, url_prefix="/api/v1")


def _is_admin() -> bool:
    return getattr(current_user, "app_role", None) == "admin"


@bp.get("/school")
@login_required
def list_schools():
    include_disabled = _is_admin() and request.args.get("includeDisabled", "").strip().lower() in {
        "1", "true", "yes", "on",
    }
    q = request.args.get("q")
    schools = SchoolService().list_schools(q=q or None, include_disabled=include_disabled)
    return ok({"items": [SchoolOut.from_school(s).to_dict() for s in schools]})


@bp.post("/school")
@login_required
def create_school():
    # Any signed-in user may add a school — duplicates are rejected by the
    # normalized-name check in the service (409 school_already_exists).
    service = SchoolService()
    dto = SchoolCreateIn.validate(request.get_json(silent=True) or {})
    school = service.create_school(dto, actor_id=current_user.id)
    return created(SchoolOut.from_school(school).to_dict())


@bp.patch("/school/<string:school_id>")
@login_required
def update_school(school_id: str):
    if denied := require_role("admin"):
        return denied
    dto = SchoolUpdateIn.validate(request.get_json(silent=True) or {})
    school = SchoolService().update_school(school_id, dto, actor_id=current_user.id)
    return ok(SchoolOut.from_school(school).to_dict())


@bp.get("/city")
@login_required
def list_cities():
    cities = CityService().list_cities()
    return ok({"items": [CityOut.from_city(c).to_dict() for c in cities]})
