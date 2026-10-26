"""Account input DTOs — request-body validation for account endpoints."""
from __future__ import annotations

from pydantic import field_validator, model_validator

from app.infra.validation import EMAIL_PATTERN
from framework.base import DTOBase

VALID_APP_ROLES = ("user", "admin")


class UserCreateIn(DTOBase):
    """Validate an admin user-creation payload."""

    email: str = DTOBase.field(..., max_length=255)
    username: str | None = DTOBase.field(None, min_length=3, max_length=150)
    password: str = DTOBase.field(..., min_length=6, max_length=255)
    full_name: str = DTOBase.field(..., alias="fullName", max_length=255)
    app_role: str = DTOBase.field("user", alias="appRole")
    role_names: list[str] | None = DTOBase.field(None, alias="roleNames")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("invalid_email")
        return value

    @field_validator("app_role")
    @classmethod
    def validate_app_role(cls, v: str) -> str:
        if v not in VALID_APP_ROLES:
            raise ValueError("invalid_app_role")
        return v

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("required")
        return v

    @model_validator(mode="after")
    def fill_username(self):
        if not self.username:
            self.username = self.email
        return self


class UserUpdateIn(DTOBase):
    """Validate a user admin-update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    username: str | None = DTOBase.field(default=None, min_length=3, max_length=150)
    full_name: str | None = DTOBase.field(default=None, alias="fullName", min_length=1, max_length=255)
    active: bool | None = DTOBase.field(default=None, alias="isActive")
    app_role: str | None = DTOBase.field(default=None, alias="appRole")
    role_names: list[str] | None = DTOBase.field(default=None, alias="roleNames")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not all(ch.isalnum() or ch in "_.-" for ch in v):
            raise ValueError("invalid_username")
        return v

    @field_validator("app_role")
    @classmethod
    def validate_app_role(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_APP_ROLES:
            raise ValueError("invalid_app_role")
        return v

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


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


__all__ = ["ApiKeyCreateIn", "RoleCreateIn", "RoleUpdateIn", "UserCreateIn", "UserUpdateIn"]
