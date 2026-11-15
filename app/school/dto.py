"""Master data input DTOs — school admin validation."""
from __future__ import annotations

from pydantic import field_validator, model_validator

from framework.base import DTOBase


class SchoolCreateIn(DTOBase):
    """Validate an admin-created school payload (name + master city)."""

    name: str = DTOBase.field(..., min_length=3, max_length=140)
    city_id: str = DTOBase.field(..., alias="cityId", min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        if not isinstance(value, str):
            return value
        value = " ".join(value.strip().split())
        if len(value) < 3:
            raise ValueError("school_name_too_short")
        return value


class SchoolUpdateIn(DTOBase):
    """Validate an admin school update payload (rename / move / (de)activate)."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    name: str | None = DTOBase.field(default=None, min_length=3, max_length=140)
    is_active: bool | None = DTOBase.field(default=None, alias="isActive")
    city_id: str | None = DTOBase.field(default=None, alias="cityId", min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        if value is None:
            return value
        if not isinstance(value, str):
            return value
        return " ".join(value.strip().split())

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


__all__ = [
    "SchoolCreateIn",
    "SchoolUpdateIn",
]
