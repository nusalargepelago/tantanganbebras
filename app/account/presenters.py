"""Account presenters — serialization for account management responses."""
from __future__ import annotations

from app.account.models import ApiKey
from app.auth.models import Role
from app.auth.presenters import UserOut
from framework.base import PresenterBase


class UserAdminOut(UserOut):
    """Admin-facing user response — same contract, admin-scoped name."""


class RoleOut(PresenterBase):
    """Role response."""

    id: str
    name: str

    @classmethod
    def from_role(cls, role: Role) -> RoleOut:
        return cls.from_model(role)


class ApiKeyOut(PresenterBase):
    """API key response — never exposes the raw secret."""

    id: str
    name: str
    prefix: str
    is_active: bool = PresenterBase.field(True, alias="isActive")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")

    @classmethod
    def from_api_key(cls, key: ApiKey) -> ApiKeyOut:
        return cls.from_model(key, name=key.masked_name)


class MenuPreferenceOut(PresenterBase):
    """Per-user menu order and visibility."""

    order: list[str] = PresenterBase.field(default_factory=list)
    hidden: list[str] = PresenterBase.field(default_factory=list)


__all__ = ["ApiKeyOut", "MenuPreferenceOut", "RoleOut", "UserAdminOut"]
