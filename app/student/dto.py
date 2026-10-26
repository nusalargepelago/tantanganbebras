"""Student input DTOs — validation for student auth, CRUD, and import."""
from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from app.infra.validation import EMAIL_PATTERN
from framework.base import DTOBase

Category = Literal["cub", "scout", "rover"]
StudentStatus = Literal["Active", "Inactive"]


class _StudentBase(DTOBase):
    """Shared email / username / name normalisation for student payloads."""

    email: str = DTOBase.field(..., max_length=320)
    username: str = DTOBase.field(..., min_length=3, max_length=80)
    first_name: str = DTOBase.field(..., alias="firstName", min_length=1, max_length=80)
    last_name: str = DTOBase.field(..., alias="lastName", min_length=1, max_length=80)
    category: Category = DTOBase.field(...)
    school: str | None = DTOBase.field(None, max_length=140)
    city: str | None = DTOBase.field(None, max_length=80)
    country: str | None = DTOBase.field("Indonesia", max_length=80)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("invalid_email")
        return value

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip() if isinstance(value, str) else value


class StudentRegisterIn(_StudentBase):
    """Validate a student self-registration payload (no password strength)."""

    password: str = DTOBase.field(..., min_length=6, max_length=255)


class StudentLoginIn(DTOBase):
    """Validate a student login payload."""

    username: str = DTOBase.field(..., min_length=1, max_length=80)
    password: str

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip() if isinstance(value, str) else value


class StudentCreateIn(_StudentBase):
    """Validate an admin-created student payload."""

    password: str = DTOBase.field(..., min_length=6, max_length=255)
    status: StudentStatus = DTOBase.field("Inactive")


class StudentUpdateIn(DTOBase):
    """Validate a student update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    email: str | None = DTOBase.field(None, max_length=320)
    username: str | None = DTOBase.field(None, min_length=3, max_length=80)
    first_name: str | None = DTOBase.field(None, alias="firstName", min_length=1, max_length=80)
    last_name: str | None = DTOBase.field(None, alias="lastName", min_length=1, max_length=80)
    password: str | None = DTOBase.field(None, min_length=6, max_length=255)
    category: Category | None = DTOBase.field(None)
    school: str | None = DTOBase.field(None, max_length=140)
    city: str | None = DTOBase.field(None, max_length=80)
    country: str | None = DTOBase.field(None, max_length=80)
    status: StudentStatus | None = DTOBase.field(None)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if value is None or not isinstance(value, str):
            return value
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("invalid_email")
        return value

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


__all__ = [
    "Category",
    "StudentCreateIn",
    "StudentLoginIn",
    "StudentRegisterIn",
    "StudentStatus",
    "StudentUpdateIn",
]
