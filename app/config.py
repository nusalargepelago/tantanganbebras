"""Application configuration for Minimals."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from framework.infra.config import BaseConfig

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
load_dotenv(BASE_DIR.parent / ".env")


def _database_url() -> str:
    """Resolve DATABASE_URL; relative sqlite paths live under data/ (volume-friendly)."""
    uri = os.environ.get("DATABASE_URL", "") or "sqlite:///app.db"
    if uri.startswith("sqlite:///"):
        path = uri[len("sqlite:///"):]
        is_absolute = (
            not path
            or path == ":memory:"
            or path.startswith("/")
            or (len(path) > 1 and path[1] == ":")
        )
        if not is_absolute:
            resolved = DATA_DIR / path
            try:
                resolved.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass
            return f"sqlite:///{resolved.as_posix()}"
    return uri


class Config(BaseConfig):
    SQLALCHEMY_DATABASE_URI = _database_url()

    STATIC_FOLDER = str(BASE_DIR / "static")
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")

    SPA_STATIC_ROOT = str(BASE_DIR / "static" / "frontend")
    SPA_URL_PREFIX = ""

    # --- SEO / white-label ----------------------------------------------------
    # index.html is the only HTML crawlers see: the brand name, tagline,
    # description and siteUrl live in the settings table (set during setup)
    # and are injected server-side. These two knobs only come from the env.
    SEO_INDEXABLE = os.environ.get("SEO_INDEXABLE", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    APP_LANG = os.environ.get("APP_LANG", "en")

    # --- Security headers -----------------------------------------------------
    # Legacy question images are hosted on Google's CDN, so this app widens the
    # framework default beyond 'self' and data: URIs. Keep the framework layer
    # generic; per-deployment overrides still go through TALISMAN_CSP.
    TALISMAN_CSP = os.environ.get("TALISMAN_CSP", "") or (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://*.googleusercontent.com; "
        "font-src 'self'; base-uri 'self'; object-src 'none'"
    )

    # data/ is the only writable path in the container (and is git-ignored),
    # so the default log has to live there — app/logs/ is not created by the
    # image and would raise PermissionError for the non-root user.
    LOG_FILE = os.environ.get("LOG_FILE", str(DATA_DIR / "app.log"))
