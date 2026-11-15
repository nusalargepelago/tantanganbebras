"""Brand settings input DTOs — request-body validation."""
from __future__ import annotations

from pydantic import field_validator

from app.infra.uploads import upload_name_from_url
from framework.base import DTOBase


class BrandLogoIn(DTOBase):
    """Validate a brand logo update payload.

    An empty string clears the logo. Anything else must be a stored
    upload URL, so the value can never point at an arbitrary host.
    """

    logo_url: str = DTOBase.field(..., alias="logoUrl", max_length=512)

    @field_validator("logo_url")
    @classmethod
    def validate_logo_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        if upload_name_from_url(value) is None:
            raise ValueError("invalid")
        return value


__all__ = ["BrandLogoIn"]
