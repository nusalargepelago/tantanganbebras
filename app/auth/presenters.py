"""Auth presenter — end-user serialization for user responses."""
from __future__ import annotations

from typing import Self

from app.auth.models import User
from framework.base import PresenterBase


class UserOut(PresenterBase):
    """Serialized user response."""

    id: str
    email: str
    username: str
    full_name: str = PresenterBase.field("", alias="fullName")
    app_role: str | None = PresenterBase.field(None, alias="appRole")
    roles: list[str] = PresenterBase.field(default_factory=list)
    is_active: bool = PresenterBase.field(True, alias="isActive")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")

    @classmethod
    def from_user(cls, user: User) -> Self:
        return cls.from_model(user, roles=[r.name for r in user.roles])


__all__ = ["UserOut"]
