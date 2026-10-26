"""Preference endpoints — per-user navigation menu layout."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.account.dto import MenuPreferenceIn
from app.account.presenters import MenuPreferenceOut
from app.account.services import MenuPreference, PreferenceService
from framework.api import BlueprintFactory, ok

bp = BlueprintFactory("account_preference", __name__, url_prefix="/api/v1/account")


def _serialize(preference: MenuPreference) -> dict:
    return MenuPreferenceOut(
        order=preference.order, hidden=preference.hidden
    ).to_dict()


@bp.get("/menu-preferences")
@login_required
def get_menu_preference():
    return ok(_serialize(PreferenceService().get_menu(current_user.id)))


@bp.put("/menu-preferences")
@login_required
def save_menu_preference():
    dto = MenuPreferenceIn.validate(request.get_json(silent=True) or {})
    return ok(_serialize(PreferenceService().save_menu(current_user.id, dto)))


__all__ = ["bp"]
