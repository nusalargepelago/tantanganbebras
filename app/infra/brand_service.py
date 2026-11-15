"""Brand settings service — global white-label updates."""
from __future__ import annotations

import logging
from pathlib import Path

from flask import current_app

from app.infra.repositories import SettingRepository
from app.infra.seo import LOGO_KEY
from app.infra.uploads import upload_name_from_url
from framework.base import ServiceBase
from framework.exceptions import ValidationFailed

logger = logging.getLogger(__name__)


class BrandService(ServiceBase[SettingRepository]):
    """Owns brand rules; the blueprint only translates HTTP."""

    repository_class = SettingRepository

    def get_logo(self) -> str:
        row = self._repo.get(LOGO_KEY)
        return row.value if row and row.value else ""

    def save_logo(self, url: str) -> str:
        if url:
            self._require_stored_upload(url)
        previous = self.get_logo()
        self._repo.set(LOGO_KEY, url)
        self._commit()
        if previous and previous != url:
            self._delete_upload(previous)
        return url

    @staticmethod
    def _require_stored_upload(url: str) -> None:
        name = upload_name_from_url(url)
        folder = Path(current_app.config["UPLOAD_FOLDER"])
        if name is None or not (folder / name).is_file():
            raise ValidationFailed("logo_upload_missing")

    @staticmethod
    def _delete_upload(url: str) -> None:
        name = upload_name_from_url(url)
        if name is None:
            return
        folder = Path(current_app.config["UPLOAD_FOLDER"])
        try:
            (folder / name).unlink(missing_ok=True)
        except OSError:
            logger.warning("could not delete replaced logo %s", name, exc_info=True)


__all__ = ["BrandService"]
