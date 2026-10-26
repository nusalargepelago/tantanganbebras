"""Todo presenters — wire serialization for todos."""
from __future__ import annotations

from app.infra.presenters import UtcPresenterBase
from app.todos.models import Todo
from framework.base import PresenterBase


class TodoOut(UtcPresenterBase):
    """Todo on the wire."""

    id: str
    title: str
    description: str | None = PresenterBase.field(None)
    completed: bool = PresenterBase.field(False)
    due_date: str | None = PresenterBase.field(None, alias="dueDate")
    creator_id: str = PresenterBase.field(alias="creatorId")
    created_at: str | None = PresenterBase.field(None, alias="createdAt")
    updated_at: str | None = PresenterBase.field(None, alias="updatedAt")

    @classmethod
    def from_todo(cls, todo: Todo) -> TodoOut:
        return cls.from_model(todo)


__all__ = ["TodoOut"]
