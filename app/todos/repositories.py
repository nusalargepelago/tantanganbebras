"""Todo repositories — query layer for todos."""
from __future__ import annotations

from app.todos.models import Todo
from framework.base import RepositoryBase
from framework.extensions import db


class TodoRepository(RepositoryBase[Todo]):
    """Query layer for todos."""

    model = Todo

    def list_todos(
        self,
        *,
        search: str | None = None,
        completed: bool | None = None,
        creator_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Todo], int]:
        query = db.session.query(Todo)
        if creator_id is not None:
            query = query.filter(Todo.creator_id == creator_id)
        if completed is not None:
            query = query.filter(Todo.completed.is_(completed))
        if search:
            query = query.filter(Todo.title.ilike(f"%{search}%"))
        total = query.count()
        items = (
            query.order_by(Todo.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["TodoRepository"]
