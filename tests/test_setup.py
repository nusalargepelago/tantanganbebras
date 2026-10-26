from __future__ import annotations

import pytest

from app.infra.db_bootstrap import db_error_key


class _FakeDBError(Exception):
    """Stands in for a driver error, which carries its SQLSTATE in ``orig``."""

    def __init__(self, message: str, code):
        super().__init__(message)
        self.orig = type("Orig", (), {"args": (code,)})()


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (_FakeDBError("Access denied for user", 1045), "invalid_db_credentials"),
        (_FakeDBError("password authentication failed", "28P01"),
         "invalid_db_credentials"),
        (_FakeDBError("Can't connect to MySQL server", 2003), "db_unreachable"),
        (_FakeDBError("connection timed out", None), "db_timeout"),
        (_FakeDBError("Name or service not known", None), "unknown_db_host"),
        (_FakeDBError("something else entirely", None), "db_connection_failed"),
    ],
)
def test_db_error_key_returns_snake_case(exc, expected):
    assert db_error_key(exc) == expected


def test_db_test_allowed_from_loopback(client, tmp_path):
    target = tmp_path / "probe.db"
    response = client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite", "path": str(target)},
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "ok": True,
        "engine": "sqlite",
        "url": f"sqlite:///{str(target).replace(chr(92), '/')}",
    }


def test_db_test_blocked_from_public_client(client):
    client.environ_base["REMOTE_ADDR"] = "8.8.8.8"
    response = client.post("/api/v1/setup/db-test", json={"engine": "sqlite"})
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_db_test_blocked_from_private_network(client):
    client.environ_base["REMOTE_ADDR"] = "192.168.1.10"
    response = client.post("/api/v1/setup/db-test", json={"engine": "sqlite"})
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_setup_run_blocked_from_public_client(client):
    client.environ_base["REMOTE_ADDR"] = "8.8.8.8"
    response = client.post(
        "/api/v1/setup",
        json={"admin": {"email": "boss@example.com", "password": "Str0ng!Pass",
                        "fullName": "Boss User"}},
    )
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_setup_blocked_when_forwarded_client_is_public(client):
    client.environ_base["REMOTE_ADDR"] = "127.0.0.1"
    response = client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite"},
        headers={"X-Forwarded-For": "8.8.8.8"},
    )
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_setup_blocked_when_forwarded_loopback_is_spoofed(client):
    client.environ_base["REMOTE_ADDR"] = "8.8.8.8"
    response = client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite"},
        headers={"X-Forwarded-For": "127.0.0.1"},
    )
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_db_test_blocks_link_local_target(client):
    response = client.post(
        "/api/v1/setup/db-test",
        json={
            "engine": "postgresql",
            "host": "169.254.169.254",
            "database": "meta",
            "username": "u",
            "password": "p",
        },
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "unsupported_host"}


def test_db_test_rejects_relative_sqlite_path(client):
    response = client.post(
        "/api/v1/setup/db-test", json={"engine": "sqlite", "path": "app.db"}
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "invalid_db_path"}


def test_db_test_rejects_sqlite_path_traversal(client):
    response = client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite", "path": "/var/lib/../../etc/passwd"},
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "invalid_db_path"}


def test_db_test_rejects_host_injection(client):
    response = client.post(
        "/api/v1/setup/db-test",
        json={
            "engine": "postgresql",
            "host": "db.internal@evil.example",
            "database": "app",
            "username": "u",
            "password": "p",
        },
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "invalid_db_host"}


def test_db_test_rejects_database_path_injection(client):
    response = client.post(
        "/api/v1/setup/db-test",
        json={
            "engine": "postgresql",
            "host": "localhost",
            "database": "app/../other",
            "username": "u",
            "password": "p",
        },
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "invalid_db_name"}


def test_setup_rejects_weak_admin_password(client):
    response = client.post(
        "/api/v1/setup",
        json={
            "db": {"engine": "sqlite", "path": "/tmp/minimals-rejected.db"},
            "admin": {
                "email": "boss@example.com",
                "password": "aaaaaaaa",
                "fullName": "Boss User",
            },
        },
    )
    assert response.status_code == 400
    assert response.get_json()["message"].endswith(
        "password_must_contain_uppercase"
    )


def test_setup_rejects_blank_admin_username(client):
    response = client.post(
        "/api/v1/setup",
        json={
            "db": {"engine": "sqlite", "path": "/tmp/minimals-rejected.db"},
            "admin": {
                "email": "boss@example.com",
                "username": "   ",
                "password": "Str0ng!Pass",
                "fullName": "Boss User",
            },
        },
    )
    assert response.status_code == 400
    assert response.get_json()["message"].endswith(
        "username_must_be_at_least_3_characters"
    )


@pytest.fixture()
def restore_engine(app):
    """Put the original engine back.

    The ``app`` fixture drops every table and disposes the engine on teardown.
    A test that re-points the engine at another database would otherwise make
    that teardown wipe the wrong file.
    """
    from framework.extensions import db

    with app.app_context():
        original = db._app_engines[app].get(None)
        original_url = app.config["SQLALCHEMY_DATABASE_URI"]
        yield
        db.session.remove()
        db._app_engines[app][None] = original
        app.config["SQLALCHEMY_DATABASE_URI"] = original_url


def test_setup_repoints_engine_without_restart(client, app, tmp_path, restore_engine):
    """The wizard switches the live engine, so no restart is needed.

    This is the whole point of the change: the seeded admin must be readable
    through the *application* engine on the very next query, in the same
    process that was started against the old database.
    """
    from app.auth.models import User
    from framework.extensions import db

    target = tmp_path / "switched.db"

    response = client.post(
        "/api/v1/setup",
        json={
            "db": {"engine": "sqlite", "path": str(target)},
            "admin": {
                "email": "boss@example.com",
                "username": "boss",
                "password": "Str0ng!Pass",
                "fullName": "Boss User",
            },
        },
    )
    assert response.status_code == 201, response.get_json()
    assert response.get_json()["restartRequired"] is False

    # The application engine now points at the new file...
    with app.app_context():
        assert db.engine.url.database == target.as_posix()
        # ...and the admin the wizard seeded is immediately readable through it.
        seeded = db.session.scalar(
            db.select(User).where(User.email == "boss@example.com")
        )
        assert seeded is not None
        assert seeded.app_role == "admin"

    # The wizard rewrote DATABASE_URL, so a later restart agrees with the swap.
    assert app.config["SQLALCHEMY_DATABASE_URI"].endswith("switched.db")


def test_setup_after_repoint_reports_complete(client, app, tmp_path, restore_engine):
    """Once re-pointed, status flips to complete without a restart.

    Before the swap this needed a restart; that is what let the wizard be
    re-run against a fresh database.
    """
    target = tmp_path / "complete.db"
    response = client.post(
        "/api/v1/setup",
        json={
            "db": {"engine": "sqlite", "path": str(target)},
            "admin": {
                "email": "boss@example.com",
                "username": "boss",
                "password": "Str0ng!Pass",
                "fullName": "Boss User",
            },
        },
    )
    assert response.status_code == 201, response.get_json()

    status = client.get("/api/v1/setup/status").get_json()
    assert status["setupRequired"] is False
    assert status["reason"] is None


def _setup_payload(target, brand=None, lang=None):
    payload = {
        "db": {"engine": "sqlite", "path": str(target)},
        "admin": {
            "email": "boss@example.com",
            "username": "boss",
            "password": "Str0ng!Pass",
            "fullName": "Boss User",
        },
    }
    if brand is not None:
        payload["brand"] = brand
    if lang is not None:
        payload["lang"] = lang
    return payload


def test_setup_seeds_brand(client, app, tmp_path, restore_engine):
    from app.infra.seo import get_brand

    target = tmp_path / "branded.db"
    response = client.post(
        "/api/v1/setup",
        json=_setup_payload(
            target,
            {
                "name": "Acme Corp",
                "tagline": "Work less",
                "description": "Acme helps you work less.",
                "siteUrl": "https://acme.test",
            },
        ),
    )
    assert response.status_code == 201, response.get_json()

    with app.app_context():
        assert get_brand() == {
            "name": "Acme Corp",
            "tagline": "Work less",
            "description": "Acme helps you work less.",
            "siteUrl": "https://acme.test",
        }


def test_setup_defaults_brand_when_omitted(client, app, tmp_path, restore_engine):
    from app.infra.seo import get_brand

    target = tmp_path / "plain.db"
    response = client.post("/api/v1/setup", json=_setup_payload(target))
    assert response.status_code == 201, response.get_json()

    with app.app_context():
        assert get_brand()["name"] == "Tantangan Bebras"


def test_setup_seeds_app_lang(client, app, tmp_path, restore_engine):
    from app.infra.seo import get_app_lang

    target = tmp_path / "lang-id.db"
    response = client.post("/api/v1/setup", json=_setup_payload(target, lang="id"))
    assert response.status_code == 201, response.get_json()

    with app.app_context():
        assert get_app_lang() == "id"


def test_setup_defaults_app_lang_when_omitted(client, app, tmp_path, restore_engine):
    from app.infra.seo import get_app_lang

    target = tmp_path / "lang-default.db"
    response = client.post("/api/v1/setup", json=_setup_payload(target))
    assert response.status_code == 201, response.get_json()

    with app.app_context():
        assert get_app_lang() == "en"


def test_setup_rejects_unsupported_lang(client):
    response = client.post(
        "/api/v1/setup",
        json=_setup_payload("/tmp/minimals-rejected.db", lang="fr"),
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "unsupported_lang"}


@pytest.mark.parametrize(
    "site_url",
    [
        "javascript:alert(1)",
        "https:// ",
        "https://exam ple",
        "https://[bad",
        "ftp://acme.test",
        "//acme.test",
    ],
)
def test_setup_rejects_invalid_site_url(client, site_url):
    response = client.post(
        "/api/v1/setup",
        json=_setup_payload(
            "/tmp/minimals-rejected.db",
            {"name": "Acme", "siteUrl": site_url},
        ),
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "site_url_invalid"}
