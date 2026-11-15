"""Shared credential validation for every DTO carrying login fields.

Cross-domain: both the register path and the first-run setup wizard accept an
email, a username and a password, so the rules live here instead of being
duplicated per DTO. Field-level bounds (min/max length) stay on the DTO —
this module owns policy, not shape.
"""
from __future__ import annotations

import re

from pydantic import field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+$")
PASSWORD_SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"


class UsernamePolicy:
    """Username normalisation + charset rule.

    Normalised in ``mode="before"`` so declared length bounds apply to the
    cleaned value rather than to the raw input.
    """

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        if not isinstance(value, str):
            return value
        return value.strip().lower()

    @field_validator("username")
    @classmethod
    def check_username_charset(cls, value):
        if value is not None and not all(
            ch.isalnum() or ch in "_.-" for ch in value
        ):
            raise ValueError("invalid_username")
        return value


class CredentialPolicy(UsernamePolicy):
    """Validation mixin for email / password / full_name.

    Username rules come from :class:`UsernamePolicy`. Email is normalised in
    ``mode="before"`` so declared length bounds apply to the cleaned value
    rather than to the raw input.
    """

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("invalid_email")
        return value

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value):
        if not any(ch.isupper() for ch in value):
            raise ValueError("password_must_contain_uppercase")
        if not any(ch.islower() for ch in value):
            raise ValueError("password_must_contain_lowercase")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("password_must_contain_digit")
        if not any(ch in PASSWORD_SPECIAL for ch in value):
            raise ValueError("password_must_contain_special_character")
        return value

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, value):
        if not value.strip():
            raise ValueError("required")
        return value


__all__ = ["EMAIL_PATTERN", "PASSWORD_SPECIAL", "CredentialPolicy", "UsernamePolicy"]
