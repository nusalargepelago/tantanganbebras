"""White-label brand + SEO — settings storage, index payload, crawler files."""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

from flask import Blueprint, current_app, has_request_context, request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.models import AppSetting
from framework.exceptions import ValidationFailed
from framework.extensions import db
from framework.extensions.rate_limit import limiter

bp = Blueprint("seo", __name__)

limiter.exempt(bp)

DEFAULT_BRAND: dict[str, str] = {
    "name": "Tantangan Bebras",
    "tagline": "",
    "description": "",
    "siteUrl": "",
}

BRAND_KEYS = tuple(DEFAULT_BRAND)


def get_brand() -> dict[str, str]:
    """Current brand settings; never raises.

    Before setup (no schema) or on any storage error the defaults are
    returned so serving ``index.html`` keeps working.
    """
    brand = dict(DEFAULT_BRAND)
    try:
        rows = db.session.scalars(
            select(AppSetting).where(AppSetting.key.in_(BRAND_KEYS))
        ).all()
    except Exception:
        db.session.rollback()
        return brand
    brand.update({row.key: row.value for row in rows})
    if not brand["name"].strip():
        brand["name"] = DEFAULT_BRAND["name"]
    return brand


def save_brand(session: Session, brand: dict[str, str]) -> None:
    """Upsert brand rows into the given (setup) session."""
    for key in BRAND_KEYS:
        value = (brand.get(key) or "").strip()
        if key == "name" and not value:
            value = DEFAULT_BRAND["name"]
        row = session.execute(
            select(AppSetting).where(AppSetting.key == key)
        ).scalar_one_or_none()
        if row is None:
            session.add(AppSetting(key=key, value=value))
        else:
            row.value = value


def validate_site_url(url: str | None) -> None:
    """Site URL must be an absolute http(s) URL with no whitespace."""
    if not url:
        return
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
    except ValueError:
        raise ValidationFailed("site_url_invalid") from None
    if (
        parts.scheme not in ("http", "https")
        or not hostname
        or any(ch.isspace() for ch in url)
    ):
        raise ValidationFailed("site_url_invalid")


SUPPORTED_LANGS = ("en", "id")
APP_LANG_KEY = "appLang"


def _default_app_lang() -> str:
    lang = (current_app.config.get("APP_LANG") or "en").strip().lower()
    return lang if lang in SUPPORTED_LANGS else "en"


def get_app_lang() -> str:
    """App-wide default language from settings; never raises.

    Falls back to ``APP_LANG`` (then ``en``) before setup or on any
    storage error so serving ``index.html`` keeps working.
    """
    try:
        row = db.session.scalar(
            select(AppSetting).where(AppSetting.key == APP_LANG_KEY)
        )
    except Exception:
        db.session.rollback()
        return _default_app_lang()
    if row is None:
        return _default_app_lang()
    lang = (row.value or "").strip().lower()
    return lang if lang in SUPPORTED_LANGS else _default_app_lang()


def save_app_lang(session: Session, lang: str) -> None:
    """Upsert the app language row into the given (setup) session."""
    row = session.execute(
        select(AppSetting).where(AppSetting.key == APP_LANG_KEY)
    ).scalar_one_or_none()
    if row is None:
        session.add(AppSetting(key=APP_LANG_KEY, value=lang))
    else:
        row.value = lang


def _request_lang() -> str:
    """Visitor language: the SPA's ``minimals-lang`` cookie, else the app default."""
    if has_request_context():
        lang = (request.cookies.get("minimals-lang") or "").strip().lower()
        if lang in SUPPORTED_LANGS:
            return lang
    return get_app_lang()


def _canonical(brand: dict[str, str] | None = None) -> str:
    """Absolute site URL from brand ``siteUrl``; empty when not configured.

    Never derived from the request ``Host`` header — a spoofed host must
    not poison canonical/OG/sitemap URLs.
    """
    if brand is None:
        brand = get_brand()
    return brand.get("siteUrl", "").rstrip("/")


def _indexable() -> bool:
    return bool(current_app.config.get("SEO_INDEXABLE", True))


def index_context() -> dict:
    """Boot payload for ``index.html``: brand + app language for the SPA, seo for the head.

    ``seo`` is consumed server-side (``_apply_seo``) and never becomes a
    window global; everything else lands on a window global
    (``window.brand``, ``window.appLang``).
    """
    brand = get_brand()
    description = brand.get("description") or brand.get("tagline") or ""
    seo = {
        "title": brand["name"],
        "lang": _request_lang(),
        "description": description,
        "robots": "index, follow" if _indexable() else "noindex, nofollow",
        "canonical": _canonical(brand),
    }
    return {"brand": brand, "seo": seo, "appLang": get_app_lang()}


@bp.get("/robots.txt")
def robots_txt():
    if _indexable():
        body = "User-Agent: *\nAllow: /\nDisallow: /api/\n"
        if canonical := _canonical():
            body += f"Sitemap: {canonical}/sitemap.xml\n"
    else:
        body = "User-Agent: *\nDisallow: /\n"
    return body, 200, {"Content-Type": "text/plain; charset=utf-8"}


@bp.get("/sitemap.xml")
def sitemap_xml():
    canonical = _canonical()
    loc = escape(f"{canonical}/") if canonical else ""
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + (f"  <url><loc>{loc}</loc></url>\n" if loc else "")
        + "</urlset>\n"
    )
    return xml, 200, {"Content-Type": "application/xml; charset=utf-8"}


__all__ = [
    "APP_LANG_KEY",
    "BRAND_KEYS",
    "DEFAULT_BRAND",
    "SUPPORTED_LANGS",
    "bp",
    "get_app_lang",
    "get_brand",
    "index_context",
    "save_app_lang",
    "save_brand",
    "validate_site_url",
]
