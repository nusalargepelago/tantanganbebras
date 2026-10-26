from __future__ import annotations

import os

import pytest
from flask import Flask

from framework.infra.config import _engine_options, _scoped_cookie_name


def test_engine_options_empty_for_sqlite_and_missing_uri():
    assert _engine_options("sqlite:///app.db") == {}
    assert _engine_options(None) == {}


def test_cookie_names_are_scoped_by_port():
    assert _scoped_cookie_name("session", "8000", None) == "session_8000"
    assert _scoped_cookie_name("session", "8001", None) == "session_8001"
    assert _scoped_cookie_name("remember", "8001", None) == "remember_8001"


def test_cookie_names_can_be_pinned_by_env():
    assert _scoped_cookie_name("session", "8000", "pinned") == "pinned"


def test_app_uses_the_scoped_cookie_names(app):
    port = os.environ.get("PORT", "8000")
    assert app.config["SESSION_COOKIE_NAME"] == f"session_{port}"
    assert app.config["REMEMBER_COOKIE_NAME"] == f"remember_{port}"


def test_engine_options_apply_pool_config_for_server_databases():
    options = _engine_options("postgresql://user:pass@db:5432/app")
    assert set(options) == {"pool_size", "max_overflow", "pool_timeout", "pool_recycle"}
    assert options["pool_size"] >= 1


def test_engine_options_reach_the_app(app):
    assert app.config["SQLALCHEMY_ENGINE_OPTIONS"] == {}


def test_rate_limit_config_reaches_flask_limiter(app):
    assert app.config["RATELIMIT_DEFAULT"] == app.config["RATE_LIMIT_DEFAULT"]
    assert app.config["RATELIMIT_STORAGE_URI"] == "memory://"


def test_session_cookie_is_lax_without_cross_site_cors(app):
    assert app.config["CORS_ORIGINS"] == []
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["REMEMBER_COOKIE_SAMESITE"] == "Lax"


def test_csrf_endpoint_sets_the_scoped_cookie(app):
    response = app.test_client().get("/api/v1/csrf")
    cookie = response.headers["Set-Cookie"]
    assert cookie.startswith(app.config["SESSION_COOKIE_NAME"] + "=")


def test_dead_talisman_csp_config_is_gone():
    from app.config import Config

    assert not hasattr(Config, "TALISMAN_CONTENT_SECURITY_POLICY")


def test_cors_wildcard_is_rejected_with_credentials():
    from app.create_app import _init_cors

    application = Flask(__name__)
    application.config["CORS_ORIGINS"] = ["*"]
    application.config["CORS_SUPPORTS_CREDENTIALS"] = True
    with pytest.raises(ValueError):
        _init_cors(application)


def test_cors_explicit_origins_are_accepted():
    from app.create_app import _init_cors

    application = Flask(__name__)
    application.config["CORS_ORIGINS"] = ["https://example.com"]
    application.config["CORS_SUPPORTS_CREDENTIALS"] = True
    _init_cors(application)
