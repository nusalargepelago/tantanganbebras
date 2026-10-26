"""Serve a built Vue SPA — shared, service-agnostic helper."""
from __future__ import annotations

import logging
import os
import re
from collections.abc import Callable
from html import escape

from flask import (
    Flask,
    send_from_directory,
)
from flask_wtf.csrf import generate_csrf
from jinja2 import Environment, FileSystemLoader, select_autoescape

from framework.api.response import error
from framework.extensions.rate_limit import limiter

logger = logging.getLogger(__name__)

# One Jinja env per static_root — a process may mount SPAs from different
# directories, so we cannot use a single global.
_jinja_envs: dict[str, Environment] = {}

IndexContextProvider = Callable[[], dict]


def _get_jinja_env(static_root: str) -> Environment:
    env = _jinja_envs.get(static_root)
    if env is None:
        env = Environment(
            loader=FileSystemLoader(static_root),
            autoescape=select_autoescape(["html", "xml"]),
            keep_trailing_newline=True,
        )
        _jinja_envs[static_root] = env
    return env


def has_frontend(static_root: str) -> bool:
    """``True`` when the SPA ``index.html`` exists under ``static_root``."""
    return os.path.isfile(os.path.join(static_root, "index.html"))


def _apply_seo(html: str, seo: dict) -> str:
    """Inject brand-driven SEO tags into the built ``index.html``.

    The head is rewritten at serve time (title, lang, description, robots,
    canonical, Open Graph, Twitter) so the static HTML a crawler fetches
    always reflects the current brand — no client JS required. Everything
    is HTML-escaped; empty values are skipped.
    """

    def _attr(value: str) -> str:
        return escape(value, quote=True)

    lang = (seo.get("lang") or "").strip()
    if lang:
        html = re.sub(
            r'<html\s+lang="[^"]*"',
            lambda _: f'<html lang="{_attr(lang)}"',
            html,
            count=1,
        )

    title = (seo.get("title") or "").strip()
    description = (seo.get("description") or "").strip()
    robots = (seo.get("robots") or "").strip()
    canonical = (seo.get("canonical") or "").strip()

    if title:
        tag = f"<title>{escape(title)}</title>"
        if re.search(r"<title>.*?</title>", html, flags=re.IGNORECASE | re.DOTALL):
            html = re.sub(
                r"<title>.*?</title>",
                lambda _: tag,
                html,
                count=1,
                flags=re.IGNORECASE | re.DOTALL,
            )
        else:
            html = html.replace("</head>", f"{tag}\n  </head>", 1)

    lines: list[str] = []
    if description:
        lines.append(f'<meta name="description" content="{_attr(description)}" />')
    if robots:
        lines.append(f'<meta name="robots" content="{_attr(robots)}" />')
    if canonical:
        lines.append(f'<link rel="canonical" href="{_attr(canonical)}" />')
    if title:
        lines.append('<meta property="og:type" content="website" />')
        lines.append(f'<meta property="og:site_name" content="{_attr(title)}" />')
        lines.append(f'<meta property="og:title" content="{_attr(title)}" />')
        lines.append('<meta name="twitter:card" content="summary" />')
        lines.append(f'<meta name="twitter:title" content="{_attr(title)}" />')
    if canonical:
        lines.append(f'<meta property="og:url" content="{_attr(canonical)}" />')
    if description:
        lines.append(
            f'<meta property="og:description" content="{_attr(description)}" />'
        )
        lines.append(
            f'<meta name="twitter:description" content="{_attr(description)}" />'
        )
    if lines:
        html = html.replace(
            "</head>", "\n    " + "\n    ".join(lines) + "\n  </head>", 1
        )
    return html


def _render_index_html(
    static_root: str, index_context: IndexContextProvider | None = None
) -> str:
    """Render ``<static_root>/index.html`` through Jinja, injecting boot data.

    The Vite build embeds a ``{% for key in boot %} ... {% endfor %}`` block
    that needs server-side data. Every key of the ``index_context()`` result
    becomes a ``window[key]`` global for the SPA (``csrfToken`` is always
    set last and cannot be overridden). When the context carries an ``seo``
    mapping it is additionally injected into ``<head>`` server-side; ``seo``
    itself is never exposed as a window global.
    """
    boot: dict = {}
    if index_context is not None:
        try:
            boot = dict(index_context() or {})
        except Exception:
            logger.exception("index context provider failed; serving defaults")
    boot["csrfToken"] = generate_csrf()
    seo = boot.pop("seo", None)

    env = _get_jinja_env(static_root)
    template = env.get_template("index.html")
    html = template.render(boot=boot)
    if isinstance(seo, dict):
        html = _apply_seo(html, seo)
    return html


def _serve_index(static_root: str, index_context: IndexContextProvider | None = None):
    html = _render_index_html(static_root, index_context)
    return html, 200, {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-cache",
    }


def _spa_not_built(url_prefix: str):
    return (
        {
            "message": "spa_not_built",
            "hint": (
                "Build the SPA (yarn build) so its output lands in the "
                f"service's static/frontend/ folder for prefix "
                f"'{url_prefix or '/'}'."
            ),
        },
        200,
    )


def register_spa(
    app: Flask,
    static_root: str,
    url_prefix: str = "",
    index_context: IndexContextProvider | None = None,
) -> None:
    """Mount a built SPA on ``app`` at ``url_prefix``, served from ``static_root``.

    ``url_prefix`` is ``""`` for the root SPA (answers ``/``) or a path prefix
    for a sub-mounted SPA. Endpoints are namespaced by the prefix so several
    SPAs can coexist in one process.

    ``index_context`` is called per request and its keys are injected into
    ``window`` for the SPA (see ``_render_index_html``).

    Registration order matters: mount SPAs LAST, after the API blueprints, so
    the catch-all never shadows them.
    """
    prefix = url_prefix.rstrip("/")  # "" for the root SPA, or a sub-path
    slug = prefix.strip("/").replace("/", "_") or "root"

    # 1) Built assets: <prefix>/static/frontend/<file>
    def _serve_asset(filename: str, _root: str = static_root):
        # Absolute directory so files resolve regardless of cwd / root_path.
        # Built assets use content-hashed filenames (cache-busted),
        # so a 1-hour cache is safe without stale-content risk.
        return send_from_directory(_root, filename, max_age=3600)

    app.add_url_rule(
        f"{prefix}/static/frontend/<path:filename>",
        endpoint=f"spa_asset_{slug}",
        view_func=_serve_asset,
    )
    limiter.exempt(_serve_asset)

    # 2) Client-side routes: <prefix> (bare) and <prefix>/<path:path>.
    def _spa_fallback(
        path: str | None = None,
        _root: str = static_root,
        _prefix: str = prefix,
        _index_context: IndexContextProvider | None = index_context,
    ):
        # Defensive: never serve the SPA for API paths.
        if path and path.startswith("api/"):
            return error("not_found", 404)

        if not has_frontend(_root):
            return _spa_not_built(_prefix)

        # Serve a real built file if the path maps to one; else index.html.
        if path and path != "index.html":
            requested = os.path.normpath(os.path.join(_root, path))
            root_abs = os.path.abspath(_root)
            requested_abs = os.path.abspath(requested)
            # Defense-in-depth: prevent path traversal outside static root.
            if not (
                requested_abs == root_abs
                or requested_abs.startswith(root_abs + os.sep)
            ):
                return error("not_found", 404)
            if os.path.isfile(requested):
                return _serve_asset(path, _root)

        return _serve_index(_root, _index_context)

    # Bare prefix ("" or "/"). strict_slashes=False so both "/x" and "/x/"
    # work. For the root SPA this is "/".
    app.add_url_rule(
        prefix or "/",
        endpoint=f"spa_root_{slug}",
        view_func=_spa_fallback,
        defaults={"path": None},
        strict_slashes=False,
    )
    app.add_url_rule(
        f"{prefix}/<path:path>",
        endpoint=f"spa_path_{slug}",
        view_func=_spa_fallback,
        strict_slashes=False,
    )
    limiter.exempt(_spa_fallback)

    # 3) Uploads only for the root SPA (service-owned user files).
    if prefix == "":
        def _serve_upload(filename: str):
            upload_dir = os.path.join(app.static_folder or "static", "uploads")
            return send_from_directory(upload_dir, filename)

        app.add_url_rule(
            "/uploads/<path:filename>",
            endpoint="serve_upload",
            view_func=_serve_upload,
        )
        limiter.exempt(_serve_upload)


__all__ = ["has_frontend", "register_spa"]
