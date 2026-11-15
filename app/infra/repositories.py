"""Infra repositories — key/value settings storage."""
from __future__ import annotations

from app.infra.models import AppSetting
from framework.extensions import db


class SettingRepository:
    """Transaction-agnostic access to the shared ``settings`` table."""

    def get(self, key: str) -> AppSetting | None:
        return db.session.scalar(
            db.select(AppSetting).where(AppSetting.key == key)
        )

    def set(self, key: str, value: str) -> AppSetting:
        row = self.get(key)
        if row is None:
            row = AppSetting(key=key, value=value)
            db.session.add(row)
        else:
            row.value = value
        return row


__all__ = ["SettingRepository"]
