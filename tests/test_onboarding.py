"""Onboarding classification — student or teacher after registration."""
from __future__ import annotations

from conftest import TEST_CITY_SOKONG_ID, TEST_SCHOOL_ID, TEST_SCHOOL_NAME

EMAIL = "budi@example.test"
USERNAME = "budi"
PASSWORD = "Siswa!234"


def _register(client):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": EMAIL,
            "username": USERNAME,
            "password": PASSWORD,
            "fullName": "Budi Santoso",
        },
    )


def _classify_student(client, **overrides):
    payload = {
        "firstName": "Budi",
        "lastName": "Santoso",
        "category": "cub",
        "schoolId": TEST_SCHOOL_ID,
    }
    payload.update(overrides)
    return client.post("/api/v1/onboarding/student", json=payload)


def _classify_teacher(client, **overrides):
    payload = {
        "firstName": "Budi",
        "lastName": "Santoso",
        "schoolId": TEST_SCHOOL_ID,
    }
    payload.update(overrides)
    return client.post("/api/v1/onboarding/teacher", json=payload)


# --- status --------------------------------------------------------------


def test_status_none_after_register(client):
    _register(client)
    body = client.get("/api/v1/onboarding/status").get_json()
    assert body == {"classification": "none"}


def test_status_requires_auth(client):
    assert client.get("/api/v1/onboarding/status").status_code == 401


def test_status_student_after_classification(client):
    _register(client)
    response = _classify_student(client)
    assert response.status_code == 201
    assert response.get_json() == {"classification": "student"}
    assert client.get("/api/v1/onboarding/status").get_json() == {"classification": "student"}


def test_status_teacher_after_classification(client):
    _register(client)
    response = _classify_teacher(client)
    assert response.status_code == 201
    assert response.get_json() == {"classification": "teacher"}
    assert client.get("/api/v1/onboarding/status").get_json() == {"classification": "teacher"}


# --- student path ---------------------------------------------------------


def test_student_classification_creates_inactive_student(client):
    _register(client)
    response = _classify_student(client, category="scout")
    assert response.status_code == 201

    me = client.get("/api/v1/student/auth/me").get_json()
    assert me["student"]["status"] == "Inactive"
    assert me["student"]["category"] == "scout"
    assert me["student"]["school"] == TEST_SCHOOL_NAME

    roles = client.get("/api/v1/auth/me").get_json()["roles"]
    assert "Member" in roles
    assert "Teacher" not in roles


def test_student_classification_updates_names(client):
    _register(client)
    _classify_student(client, firstName="Andi", lastName="Wijaya")
    me = client.get("/api/v1/auth/me").get_json()
    assert me["fullName"] == "Andi Wijaya"


# --- teacher path ---------------------------------------------------------


def test_teacher_classification_creates_teacher_row_and_role(client):
    _register(client)
    response = _classify_teacher(client)
    assert response.status_code == 201

    me = client.get("/api/v1/auth/me").get_json()
    assert "Teacher" in me["roles"]
    assert "Member" in me["roles"]

    from app.auth.models import User
    from app.onboarding.models import Teacher
    from framework.extensions import db

    with client.application.app_context():
        user = db.session.query(User).filter_by(email=EMAIL).one()
        teacher = db.session.get(Teacher, user.id)
        assert teacher is not None
        assert teacher.school.name == TEST_SCHOOL_NAME


def test_teacher_blocked_from_staff_only(client):
    _register(client)
    _classify_teacher(client)
    assert client.get("/api/v1/dashboard").status_code == 403
    assert client.get("/api/v1/question").status_code == 403
    # Teachers may manage students, scoped to their own school.
    assert client.get("/api/v1/student").status_code == 200


def test_student_blocked_from_staff_only(client):
    _register(client)
    _classify_student(client)
    assert client.get("/api/v1/dashboard").status_code == 403


# --- invariants -----------------------------------------------------------


def test_classification_is_permanent(client):
    _register(client)
    assert _classify_student(client).status_code == 201
    assert _classify_teacher(client).status_code == 409
    assert _classify_student(client).status_code == 409
    assert client.get("/api/v1/onboarding/status").get_json() == {"classification": "student"}


def test_teacher_then_student_is_rejected(client):
    _register(client)
    assert _classify_teacher(client).status_code == 201
    assert _classify_student(client).status_code == 409


def test_classification_payloads_are_validated(client):
    _register(client)
    missing_school = _classify_teacher(client, schoolId="")
    assert missing_school.status_code == 400

    unknown_school = _classify_student(client, schoolId="00000000-0000-4000-8000-0000000000ff")
    assert unknown_school.status_code == 400
    assert unknown_school.get_json() == {"message": "school_not_in_master"}

    bad_category = _classify_student(client, category="not-a-category")
    assert bad_category.status_code == 400


def test_client_sent_city_is_ignored(client):
    """City always follows the school — a client-supplied cityId is dropped."""
    _register(client)
    response = _classify_student(client, cityId=TEST_CITY_SOKONG_ID)
    assert response.status_code == 201

    me = client.get("/api/v1/student/auth/me").get_json()
    assert me["student"]["city"] == "Kota Mataram"


def test_admin_cannot_classify(admin):
    assert _classify_student(admin).status_code == 403
    assert _classify_student(admin).get_json() == {"message": "classification_not_applicable"}
    assert _classify_teacher(admin).status_code == 403


def test_classify_requires_auth(client):
    assert _classify_student(client).status_code == 401
    assert _classify_teacher(client).status_code == 401
