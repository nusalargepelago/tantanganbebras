"""Account HTTP endpoints — user and role management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.account.dto import RoleCreateIn, RoleUpdateIn, UserCreateIn, UserUpdateIn
from app.account.presenters import RoleOut, UserAdminOut
from app.account.services import AccountService
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    no_content,
    ok,
    paginate,
    paginated_response,
)
from framework.auth.helpers import require_role

bp = BlueprintFactory("account", __name__, url_prefix="/api/v1/account")


# Users
@bp.get("/users")
@login_required
def list_users():
    if denied := require_role("admin"):
        return denied

    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    users, total = AccountService().list_users(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [UserAdminOut.from_user(u).to_dict() for u in users],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.get("/users/<user_id>")
@login_required
def get_user(user_id: str):
    if current_user.id != user_id:
        if denied := require_role("admin"):
            return denied

    user = AccountService().get_user(user_id)
    return ok(UserAdminOut.from_user(user).to_dict())


@bp.post("/users")
@login_required
def create_user():
    if denied := require_role("admin"):
        return denied

    dto = UserCreateIn.validate(request.get_json(silent=True) or {})
    user = AccountService().create_user(dto, actor_id=current_user.id)
    return created(UserAdminOut.from_user(user).to_dict())


@bp.delete("/users/<user_id>")
@login_required
def delete_user(user_id: str):
    if denied := require_role("admin"):
        return denied

    AccountService().delete_user(user_id, actor_id=current_user.id)
    return no_content()


@bp.patch("/users/<user_id>")
@login_required
def update_user(user_id: str):
    if denied := require_role("admin"):
        return denied

    dto = UserUpdateIn.validate(request.get_json(silent=True) or {})
    user = AccountService().update_user(user_id, dto, actor_id=current_user.id)
    return ok(UserAdminOut.from_user(user).to_dict())


# Roles
@bp.get("/roles")
@login_required
def list_roles():
    if denied := require_role("admin"):
        return denied

    roles = AccountService().list_roles()
    return ok({"items": [RoleOut.from_role(r).to_dict() for r in roles]})


@bp.post("/roles")
@login_required
def create_role():
    if denied := require_role("admin"):
        return denied

    dto = RoleCreateIn.validate(request.get_json(silent=True) or {})
    role = AccountService().create_role(dto.name, actor_id=current_user.id)
    return created(RoleOut.from_role(role).to_dict())


@bp.patch("/roles/<role_id>")
@login_required
def update_role(role_id: str):
    if denied := require_role("admin"):
        return denied

    dto = RoleUpdateIn.validate(request.get_json(silent=True) or {})
    role = AccountService().update_role(role_id, dto, actor_id=current_user.id)
    return ok(RoleOut.from_role(role).to_dict())


@bp.delete("/roles/<role_id>")
@login_required
def delete_role(role_id: str):
    if denied := require_role("admin"):
        return denied

    AccountService().delete_role(role_id, actor_id=current_user.id)
    return no_content()
