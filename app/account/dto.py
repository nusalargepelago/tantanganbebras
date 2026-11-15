"""Account input DTOs — request-body validation for account endpoints."""
from __future__ import annotations

from typing import TypeVar

from pydantic import field_validator, model_validator

from app.infra.validation import CredentialPolicy, UsernamePolicy
from framework.base import DTOBase

VALID_APP_ROLES = ("user", "admin")

TAppRole = TypeVar("TAppRole", bound=str | None)


def _check_app_role(v: TAppRole) -> TAppRole:
    if v is not None and v not in VALID_APP_ROLES:
        raise ValueError("invalid_app_role")
    return v


class UserUpdateIn(DTOBase, UsernamePolicy):
    """Validate a user admin-update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    username: str | None = DTOBase.field(default=None, min_length=3, max_length=150)
    full_name: str | None = DTOBase.field(default=None, alias="fullName", min_length=1, max_length=255)
    active: bool | None = DTOBase.field(default=None, alias="isActive")
    app_role: str | None = DTOBase.field(default=None, alias="appRole")
    role_names: list[str] | None = DTOBase.field(default=None, alias="roleNames")

    @field_validator("app_role")
    @classmethod
    def validate_app_role(cls, v: str | None) -> str | None:
        return _check_app_role(v)

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


class UserCreateIn(DTOBase, CredentialPolicy):
    """Validate an admin-created user payload."""

    email: str = DTOBase.field(..., max_length=255)
    username: str = DTOBase.field(..., min_length=3, max_length=150)
    password: str = DTOBase.field(..., min_length=8, max_length=255)
    full_name: str = DTOBase.field(..., alias="fullName", max_length=255)
    app_role: str = DTOBase.field(default="user", alias="appRole")
    role_names: list[str] | None = DTOBase.field(default=None, alias="roleNames")

    @field_validator("app_role")
    @classmethod
    def validate_app_role(cls, v: str) -> str:
        return _check_app_role(v)


class RoleCreateIn(DTOBase):
    """Validate a role creation payload."""

    name: str = DTOBase.field(..., min_length=1, max_length=64)


class RoleUpdateIn(DTOBase):
    """Validate a role update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    name: str | None = DTOBase.field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


class ApiKeyCreateIn(DTOBase):
    """Validate an API key creation payload."""

    name: str = DTOBase.field(..., max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name_required")
        return v


class MenuPreferenceIn(DTOBase):
    """Validate a per-user menu preference payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    order: list[str] = DTOBase.field(default_factory=list)
    hidden: list[str] = DTOBase.field(default_factory=list)

    @field_validator("order", "hidden")
    @classmethod
    def validate_keys(cls, keys: list[str]) -> list[str]:
        if len(keys) > 100:
            raise ValueError("too_many_menu_items")
        normalized = [key.strip() for key in keys]
        if any(not key or len(key) > 64 for key in normalized):
            raise ValueError("invalid_menu_key")
        if len(set(normalized)) != len(normalized):
            raise ValueError("duplicate_menu_key")
        return normalized


__all__ = [
    "ApiKeyCreateIn",
    "MenuPreferenceIn",
    "RoleCreateIn",
    "RoleUpdateIn",
    "UserCreateIn",
    "UserUpdateIn",
]
