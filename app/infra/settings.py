"""Generic key/value settings — shared accessors over the settings table."""
from __future__ import annotations

from sqlalchemy import select

from app.infra.models import AppSetting
from framework.extensions import db


def get_setting(key: str) -> str | None:
    """Current value for ``key``; never raises (``None`` when unset/broken)."""
    try:
        return db.session.scalars(
            select(AppSetting.value).where(AppSetting.key == key)
        ).one_or_none()
    except Exception:
        db.session.rollback()
        return None


def set_setting(key: str, value: str) -> str:
    """Upsert the value into the current session; the caller commits."""
    row = db.session.execute(
        select(AppSetting).where(AppSetting.key == key)
    ).scalar_one_or_none()
    if row is None:
        db.session.add(AppSetting(key=key, value=value))
    else:
        row.value = value
    db.session.flush()
    return value


__all__ = ["get_setting", "set_setting"]
