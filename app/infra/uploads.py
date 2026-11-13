"""Image upload — stores files under ``/uploads`` and returns their URL."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

from flask import current_app, request
from flask_login import login_required

from framework.api import BlueprintFactory, created, no_content
from framework.auth.helpers import require_role
from framework.exceptions import ValidationFailed
from framework.infra.uuid7 import uuid7

bp = BlueprintFactory("uploads", __name__, url_prefix="/api/v1/uploads")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
UPLOAD_URL_PREFIX = "/uploads/"


def _valid_name(name: str) -> bool:
    if "." not in name:
        return False
    stem, ext = name.rsplit(".", 1)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return False
    try:
        UUID(stem)
    except ValueError:
        return False
    return True


def upload_name_from_url(url: str) -> str | None:
    """Stored file name for a servable upload URL, else ``None``.

    Only our own ``/uploads/<uuid>.<ext>`` shape is accepted, which also
    makes the name safe to join onto ``UPLOAD_FOLDER``.
    """
    if not url.startswith(UPLOAD_URL_PREFIX):
        return None
    name = url.removeprefix(UPLOAD_URL_PREFIX)
    return name if _valid_name(name) else None


@bp.post("")
@login_required
def upload_image():
    if denied := require_role("admin"):
        return denied

    upload = (request.files or {}).get("file")
    if upload is None or not upload.filename:
        raise ValidationFailed("file_required")

    filename = upload.filename
    ext = (
        filename.rsplit(".", 1)[1].lower()
        if "." in filename
        else ""
    )
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationFailed("file_type_not_allowed")

    data = upload.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise ValidationFailed("file_too_large")

    folder = Path(current_app.config["UPLOAD_FOLDER"])
    os.makedirs(folder, exist_ok=True)
    name = f"{uuid7()}.{ext}"
    (folder / name).write_bytes(data)

    return created({"url": f"{UPLOAD_URL_PREFIX}{name}"})


@bp.delete("/<string:name>")
@login_required
def delete_image(name: str):
    if denied := require_role("admin"):
        return denied

    if not _valid_name(name):
        raise ValidationFailed("file_invalid_name")

    folder = Path(current_app.config["UPLOAD_FOLDER"])
    target = folder / name
    if target.is_file():
        target.unlink()
    return no_content()


__all__ = ["bp", "upload_name_from_url"]
