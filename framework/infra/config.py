"""Shared configuration base, read from the environment."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_load_dotenv_path = Path(__file__).resolve().parents[2] / ".env"
if _load_dotenv_path.exists():
    load_dotenv(_load_dotenv_path)


def _scoped_cookie_name(prefix: str, port: str, override: str | None) -> str:
    """Scope a cookie name by bind port; cookies themselves are host-scoped."""
    return override or f"{prefix}_{port}"


def _engine_options(uri: str | None) -> dict:
    if not uri or uri.startswith("sqlite"):
        return {}
    return {
        "pool_size": int(os.environ.get("SQLALCHEMY_POOL_SIZE", "10")),
        "max_overflow": int(os.environ.get("SQLALCHEMY_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.environ.get("SQLALCHEMY_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.environ.get("SQLALCHEMY_POOL_RECYCLE", "1800")),
    }


class BaseConfig:
    # --- Core -----------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if (
        not SECRET_KEY
        or len(SECRET_KEY) < 32
        or SECRET_KEY == "change-me-to-a-random-string-of-at-least-32-characters"
    ):
        raise ValueError(
            "SECRET_KEY must be set to a random string of at least 32 characters. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")

    # --- CORS -----------------------------------------------------------------
    CORS_ORIGINS = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
    ]
    CORS_SUPPORTS_CREDENTIALS = bool(CORS_ORIGINS)

    # --- CSRF -----------------------------------------------------------------
    WTF_CSRF_ENABLED = os.environ.get("CSRF_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    # --- Trusted reverse proxy ----------------------------------------------
    # When true, X-Forwarded-For / X-Forwarded-Proto from the nearest proxy
    # (Caddy) are trusted. Default false: a directly-exposed app must never
    # honour client-supplied X-Forwarded-* (IP spoofing / setup-wizard bypass).
    TRUSTED_PROXY = os.environ.get("TRUSTED_PROXY", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    # --- Cookies / security ---------------------------------------------------
    FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    # --- Talisman (HSTS, CSP, secure headers) -------------------------------
    if os.environ.get("TALISMAN_ENABLED", "").lower() in ("true", "1", "yes"):
        TALISMAN_ENABLED = True
    elif os.environ.get("TALISMAN_ENABLED", "").lower() in ("false", "0", "no"):
        TALISMAN_ENABLED = False
    else:
        TALISMAN_ENABLED = FORCE_HTTPS
    # Empty means "use the built-in DEFAULT_CSP", not "no policy".
    TALISMAN_CSP = os.environ.get("TALISMAN_CSP", "")

    # --- Read API gate for non-browser clients ------------------------------
    INTERNAL_API_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "")

    # --- Rate limiting ------------------------------------------------------
    RATE_LIMIT_DEFAULT = os.environ.get("RATE_LIMIT_DEFAULT", "200/hour")
    RATE_LIMIT_STORAGE_URL = os.environ.get("RATE_LIMIT_STORAGE_URL", "")
    RATE_LIMIT_AUTH = os.environ.get("RATE_LIMIT_AUTH", "10/minute")

    # --- Request size -------------------------------------------------------
    # Rejects oversized bodies before they are parsed. The auth endpoints take
    # a token anonymously, so without a cap a single request can force the
    # server to materialise an arbitrarily large JSON document. The floor is
    # set by the full-database backup restore (tens of MB) and the 5 MiB image
    # upload; tighten it in .env for deployments that disable either.
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_CONTENT_LENGTH", str(64 * 1024 * 1024))
    )

    # --- Cookie security -----------------------------------------------------
    # A cookie belongs to a host, never to a host:port, so two instances of this
    # app on one machine would otherwise share a single `session` cookie and
    # overwrite each other's login. Naming it after the bind port keeps them
    # apart while replicas of one deployment (same PORT) still share it.
    _PORT = os.environ.get("PORT", "8000").strip() or "8000"
    SESSION_COOKIE_NAME = _scoped_cookie_name(
        "session", _PORT, os.environ.get("SESSION_COOKIE_NAME")
    )
    REMEMBER_COOKIE_NAME = _scoped_cookie_name(
        "remember", _PORT, os.environ.get("REMEMBER_COOKIE_NAME")
    )
    # SameSite=None only for a cross-site API (CORS_ORIGINS set) that can
    # actually carry it — the browser rejects None without Secure.
    SESSION_COOKIE_SECURE = FORCE_HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "None" if CORS_ORIGINS and FORCE_HTTPS else "Lax"
    REMEMBER_COOKIE_SECURE = FORCE_HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE

    # --- Logging --------------------------------------------------------------
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.environ.get("LOG_FILE", "")

    # --- Alerting -------------------------------------------------------------
    # Webhook URL for alert log records (PagerDuty/Slack incoming webhook).
    # When unset (empty), no alert routing — alert logs stay in console/file only.
    ALERT_WEBHOOK_URL = os.environ.get("ALERT_WEBHOOK_URL", "")
