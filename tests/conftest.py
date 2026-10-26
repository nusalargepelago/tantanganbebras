from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="minimals_tests_"))

os.environ["DATABASE_URL"] = "sqlite:///" + str(_TMP / "test.db").replace("\\", "/")
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-x"
os.environ["CORS_ORIGINS"] = ""
os.environ["CSRF_ENABLED"] = "true"
os.environ["MIGRATE_ON_BOOT"] = "false"
os.environ["RATE_LIMIT_DEFAULT"] = "100000/hour"
os.environ["RATE_LIMIT_AUTH"] = "100000/hour"
os.environ["RATE_LIMIT_STORAGE_URL"] = ""
os.environ["INTERNAL_API_TOKEN"] = "internal-test-token"
os.environ["TALISMAN_ENABLED"] = "false"
os.environ["FORCE_HTTPS"] = "false"
os.environ["LOG_FILE"] = str(_TMP / "test.log")

REGISTER_PAYLOAD = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "Str0ng!Pass",
    "fullName": "Alice Doe",
}


def csrf_client(application):
    client = application.test_client()
    token = client.get("/api/v1/csrf").get_json()["csrfToken"]
    client.environ_base["HTTP_X_CSRFTOKEN"] = token
    return client


def register(client, **overrides):
    payload = dict(REGISTER_PAYLOAD, **overrides)
    return client.post("/api/v1/auth/register", json=payload)


@pytest.fixture(autouse=True)
def _isolate_env_file(tmp_path, monkeypatch):
    from app.infra import db_bootstrap

    monkeypatch.setattr(db_bootstrap, "env_file_path", lambda: tmp_path / ".env")


@pytest.fixture()
def app():
    from app.auth.models import Role
    from app.create_app import create_app
    from framework.extensions import db

    application = create_app()
    application.config["TESTING"] = True
    application.config["RATELIMIT_ENABLED"] = False

    with application.app_context():
        db.create_all()
        if db.session.scalar(db.select(Role).where(Role.name == "Member")) is None:
            db.session.add(Role(name="Member"))
            db.session.commit()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return csrf_client(app)


@pytest.fixture()
def member(app):
    client = csrf_client(app)
    response = register(
        client,
        email="member@example.com",
        username="member",
        fullName="Member User",
    )
    assert response.status_code == 201, response.get_json()
    return client


@pytest.fixture()
def admin(app):
    from app.auth.models import User
    from framework.extensions import db

    client = csrf_client(app)
    response = register(
        client,
        email="admin@example.com",
        username="admin",
        fullName="Admin User",
    )
    assert response.status_code == 201, response.get_json()
    user_id = response.get_json()["id"]

    with app.app_context():
        db.session.get(User, user_id).app_role = "admin"
        db.session.commit()

    return client
