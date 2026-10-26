"""Todo HTTP endpoints — CRUD with owner-or-admin RBAC."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.todos.dto import TodoCreateIn, TodoUpdateIn
from app.todos.presenters import TodoOut
from app.todos.services import TodoService
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    no_content,
    ok,
    paginate,
    paginated_response,
)
from framework.auth.helpers import require_owner_or_role
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("todos", __name__, url_prefix="/api/v1/todos")

_rate_30 = limiter.limit("30/minute")
_rate_10 = limiter.limit("10/minute")


def _serialize(todo) -> dict:
    return TodoOut.from_todo(todo).to_dict()


@bp.get("")
@login_required
def list_todos():
    page = PageIn.validate(request.args)
    args = request.args
    completed_raw = args.get("completed")
    items, total = TodoService().list_todos(
        search=(args.get("search") or None),
        completed=None if completed_raw is None else completed_raw.lower() == "true",
        actor_id=current_user.id,
        is_admin=getattr(current_user, "app_role", "user") == "admin",
        page=page.page,
        per_page=page.per_page,
    )
    return paginated_response(
        paginate([_serialize(t) for t in items], total, page.page, page.per_page)
    )


@bp.get("/<string:todo_id>")
@login_required
def get_todo(todo_id: str):
    todo = TodoService().get_todo(todo_id)
    if denied := require_owner_or_role(todo.creator_id, "admin"):
        return denied
    return ok(_serialize(todo))


@bp.post("")
@_rate_30
@login_required
def create_todo():
    dto = TodoCreateIn.validate(request.get_json(silent=True) or {})
    todo = TodoService().create_todo(dto, actor_id=current_user.id)
    return created(_serialize(todo))


@bp.patch("/<string:todo_id>")
@bp.put("/<string:todo_id>")
@_rate_30
@login_required
def update_todo(todo_id: str):
    todo = TodoService().get_todo(todo_id)
    if denied := require_owner_or_role(todo.creator_id, "admin"):
        return denied

    dto = TodoUpdateIn.validate(request.get_json(silent=True) or {})
    todo = TodoService().update_todo(todo, dto, actor_id=current_user.id)
    return ok(_serialize(todo))


@bp.delete("/<string:todo_id>")
@_rate_10
@login_required
def delete_todo(todo_id: str):
    todo = TodoService().get_todo(todo_id)
    if denied := require_owner_or_role(todo.creator_id, "admin"):
        return denied

    TodoService().delete_todo(todo, actor_id=current_user.id)
    return no_content()
