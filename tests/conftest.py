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

TEST_SCHOOL_NAME = "SMP Katolik Kesuma Mataram"
TEST_SCHOOL_ID = "00000000-0000-4000-8000-000000000001"
TEST_SCHOOL_SD_NAME = "SD Negeri 8 Sokong"
TEST_SCHOOL_SD_ID = "00000000-0000-4000-8000-000000000003"
TEST_CITY_NAME = "Kota Mataram"
TEST_CITY_ID = "00000000-0000-4000-8000-000000000002"
TEST_CITY_SOKONG_NAME = "Kabupaten Lombok Utara"
TEST_CITY_SOKONG_ID = "00000000-0000-4000-8000-000000000004"


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


def _seed_master() -> None:
    """Seed the school/city master once per test database.

    Reads the literal lists from the migration module so the test database
    mirrors production seeds. Runs only when the tables are empty.
    """
    import importlib.util
    from pathlib import Path

    from sqlalchemy import text as sa_text

    from framework.extensions import db
    from framework.infra.uuid7 import uuid7

    if db.session.execute(sa_text("SELECT COUNT(*) FROM schools")).scalar():
        return

    repo_root = Path(__file__).resolve().parent.parent
    versions = repo_root / "app" / "migrations" / "versions"

    def _load(filename: str, module_name: str):
        spec = importlib.util.spec_from_file_location(module_name, versions / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    master = _load("20261114_8_master_schools_cities.py", "master_seed")
    school_city = _load("20261114_9_school_city_id.py", "school_city_seed")

    pinned_schools = {TEST_SCHOOL_NAME: TEST_SCHOOL_ID, TEST_SCHOOL_SD_NAME: TEST_SCHOOL_SD_ID}
    pinned_cities = {TEST_CITY_NAME: TEST_CITY_ID, TEST_CITY_SOKONG_NAME: TEST_CITY_SOKONG_ID}

    from app.school.models import City, School

    city_ids: dict[str, str] = {}
    for name in master.CITIES:
        city_id = pinned_cities.get(name) or uuid7()
        city_ids[name] = city_id
        db.session.add(City(name=name, id=city_id))
    for name in master.SCHOOLS:
        city_name = school_city.SCHOOL_CITY[name]
        db.session.add(
            School(name=name, id=pinned_schools.get(name) or uuid7(), city_id=city_ids[city_name])
        )
    db.session.commit()


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
        for builtin in ("Member", "Teacher"):
            if db.session.scalar(db.select(Role).where(Role.name == builtin)) is None:
                db.session.add(Role(name=builtin))
                db.session.commit()
        _seed_master()

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


@pytest.fixture()
def teacher(client):
    """A teacher classified via the onboarding flow, scoped to TEST_SCHOOL_ID."""
    response = register(
        client,
        email="teacher@example.com",
        username="teacher",
        fullName="Guru Satu",
    )
    assert response.status_code == 201, response.get_json()
    response = client.post(
        "/api/v1/onboarding/teacher",
        json={"firstName": "Guru", "lastName": "Satu", "schoolId": TEST_SCHOOL_ID},
    )
    assert response.status_code == 201, response.get_json()
    return client
