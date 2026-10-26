"""Todo services — business logic for per-user todos."""
from __future__ import annotations

from app.infra.audit import log as audit_log
from app.todos.dto import TodoCreateIn, TodoUpdateIn
from app.todos.models import Todo
from app.todos.repositories import TodoRepository
from framework.base import ServiceBase
from framework.exceptions import NotFound


class TodoService(ServiceBase[TodoRepository]):
    """Business logic for todos."""

    repository_class = TodoRepository

    def list_todos(
        self,
        *,
        search: str | None = None,
        completed: bool | None = None,
        actor_id: str,
        is_admin: bool,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Todo], int]:
        creator_id = None if is_admin else actor_id
        return self._repo.list_todos(
            search=search,
            completed=completed,
            creator_id=creator_id,
            page=page,
            per_page=per_page,
        )

    def get_todo(self, todo_id: str) -> Todo:
        todo = self._repo.get(todo_id)
        if todo is None:
            raise NotFound("todo_not_found")
        return todo

    def create_todo(self, dto: TodoCreateIn, *, actor_id: str) -> Todo:
        todo = Todo(
            title=dto.title,
            description=dto.description,
            completed=dto.completed,
            due_date=dto.due_date,
            creator_id=actor_id,
        )
        self._repo.add(todo)
        self._flush()
        audit_log(
            "todo_created",
            user_id=actor_id,
            resource=f"todos/{todo.id}",
            details={"title": todo.title},
        )
        self._commit()
        return todo

    def update_todo(self, todo: Todo, dto: TodoUpdateIn, *, actor_id: str) -> Todo:
        data = {
            key: value
            for key, value in dto.model_dump(exclude_unset=True).items()
            if value is not None or key in {"description", "due_date"}
        }
        for key, value in data.items():
            setattr(todo, key, value)
        audit_log(
            "todo_updated",
            user_id=actor_id,
            resource=f"todos/{todo.id}",
            details={"changed": sorted(data)},
        )
        self._commit()
        return todo

    def delete_todo(self, todo: Todo, *, actor_id: str) -> None:
        audit_log(
            "todo_deleted",
            user_id=actor_id,
            resource=f"todos/{todo.id}",
            details={"title": todo.title},
        )
        self._repo.delete(todo)
        self._commit()


__all__ = ["TodoService"]
