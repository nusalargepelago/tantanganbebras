"""Account domain — re-exports bp, services, models, DTOs, and presenters."""
from __future__ import annotations

from app.account.api import bp
from app.account.dto import MenuPreferenceIn, RoleCreateIn, RoleUpdateIn, UserUpdateIn
from app.account.models import ApiKey, UserPreference
from app.account.presenters import MenuPreferenceOut, RoleOut, UserAdminOut
from app.account.services import AccountService, ApiKeyService, PreferenceService
from app.auth.models import Role, User, user_roles

__all__ = [
    "AccountService",
    "ApiKey",
    "ApiKeyService",
    "MenuPreferenceIn",
    "MenuPreferenceOut",
    "PreferenceService",
    "Role",
    "RoleCreateIn",
    "RoleOut",
    "RoleUpdateIn",
    "User",
    "UserAdminOut",
    "UserPreference",
    "UserUpdateIn",
    "bp",
    "user_roles",
]
