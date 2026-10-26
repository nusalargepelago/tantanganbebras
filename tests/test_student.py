from io import BytesIO

from conftest import csrf_client
from openpyxl import Workbook

REGISTER = {
    "firstName": "Budi",
    "lastName": "Santoso",
    "email": "budi@example.test",
    "username": "budi",
    "password": "Siswa1234",
    "category": "cub",
    "school": "SMPN 1 Bandung",
    "city": "Bandung",
}


def register_student(client, **overrides):
    return client.post(
        "/api/v1/student/auth/register",
        json=dict(REGISTER, **overrides),
    )


def build_xlsx(rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "student"
    sheet.append(
        ["first_name", "last_name", "email", "username", "password", "category",
         "school", "city", "country", "status"]
    )
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


# --- student auth -----------------------------------------------------


def test_branding_is_public(client):
    body = client.get("/api/v1/student/auth/login").get_json()
    assert body["title"] == "Tantangan Bebras"
    assert body["categoryOptions"] == ["cub", "scout", "rover"]


def test_register_creates_inactive_student(client):
    response = register_student(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["username"] == "budi"
    assert body["student"]["status"] == "Inactive"
    assert body["student"]["category"] == "cub"

    me = client.get("/api/v1/student/auth/me")
    assert me.status_code == 200
    assert me.get_json()["student"]["userId"] == body["student"]["userId"]


def test_register_duplicate_username(client):
    register_student(client)
    response = register_student(client, email="other@example.test")
    assert response.status_code == 409
    assert response.get_json() == {"message": "username_already_registered"}


def test_login_rejects_bad_password(client):
    register_student(client)
    client.post("/api/v1/student/auth/login")
    fresh = csrf_client(client.application)
    response = fresh.post(
        "/api/v1/student/auth/login",
        json={"username": "budi", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.get_json() == {"message": "invalid_credentials"}


def test_login_blocked_after_soft_delete(admin):
    student_client = csrf_client(admin.application)
    created = register_student(student_client).get_json()
    user_id = created["student"]["userId"]

    assert admin.delete(f"/api/v1/student/{user_id}").status_code == 204

    fresh = csrf_client(admin.application)
    response = fresh.post(
        "/api/v1/student/auth/login",
        json={"username": "budi", "password": "Siswa1234"},
    )
    assert response.status_code == 401
    assert response.get_json() == {"message": "invalid_credentials"}


def test_login_accepts_student_account_via_staff_login(client):
    register_student(client)

    fresh = csrf_client(client.application)
    response = fresh.post(
        "/api/v1/auth/login",
        json={"identifier": "budi", "password": "Siswa1234"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["username"] == "budi"

    me = fresh.get("/api/v1/student/auth/me")
    assert me.status_code == 200
    assert me.get_json()["student"]["userId"] == body["id"]


def test_login_wrong_password_stays_invalid_credentials(client):
    register_student(client)

    fresh = csrf_client(client.application)
    response = fresh.post(
        "/api/v1/auth/login",
        json={"identifier": "budi", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.get_json() == {"message": "invalid_credentials"}


# --- staff gate -------------------------------------------------------


def test_student_blocked_from_staff_endpoints(client):
    register_student(client)
    assert client.get("/api/v1/student").status_code == 403
    assert client.get("/api/v1/question").status_code == 403


# --- CRUD -------------------------------------------------------------


def _create_via_admin(admin, **overrides):
    payload = {
        "firstName": "Siti", "lastName": "Rani", "email": "siti@example.test",
        "username": "siti", "password": "Siswa1234", "category": "scout",
    }
    payload.update(overrides)
    return admin.post("/api/v1/student", json=payload)


def test_admin_create_and_get(admin):
    created = _create_via_admin(admin)
    assert created.status_code == 201
    body = created.get_json()
    assert body["status"] == "Inactive"
    assert body["category"] == "scout"
    assert body["username"] == "siti"

    fetched = admin.get(f"/api/v1/student/{body['userId']}")
    assert fetched.status_code == 200
    assert fetched.get_json() == body


def test_admin_list_filters_and_search(admin):
    _create_via_admin(admin)
    _create_via_admin(
        admin, username="rani", email="rani@example.test", category="rover",
        firstName="Rani", lastName="Putri",
    )

    all_students = admin.get("/api/v1/student").get_json()
    assert all_students["total"] == 2

    rover = admin.get("/api/v1/student", query_string={"category": "rover"}).get_json()
    assert rover["total"] == 1
    assert rover["items"][0]["username"] == "rani"

    found = admin.get("/api/v1/student", query_string={"q": "siti"}).get_json()
    assert found["total"] == 1


def test_activate_then_soft_delete_restore(admin):
    body = _create_via_admin(admin).get_json()
    user_id = body["userId"]

    activated = admin.post(f"/api/v1/student/{user_id}/activate")
    assert activated.status_code == 200
    assert activated.get_json()["status"] == "Active"

    assert admin.delete(f"/api/v1/student/{user_id}").status_code == 204
    listed = admin.get("/api/v1/student", query_string={"includeDisabled": "true"}).get_json()
    deleted = next(s for s in listed["items"] if s["userId"] == user_id)
    assert deleted["disabled"] is True

    restored = admin.post(f"/api/v1/student/{user_id}/restore")
    assert restored.status_code == 200
    assert restored.get_json()["disabled"] is False


def test_activate_soft_deleted_is_404(admin):
    body = _create_via_admin(admin).get_json()
    user_id = body["userId"]
    admin.delete(f"/api/v1/student/{user_id}")
    response = admin.post(f"/api/v1/student/{user_id}/activate")
    assert response.status_code == 404
    assert response.get_json() == {"message": "student_disabled"}


def test_update_student(admin):
    body = _create_via_admin(admin).get_json()
    response = admin.patch(
        f"/api/v1/student/{body['userId']}",
        json={"category": "rover", "school": "SMA 1"},
    )
    assert response.status_code == 200
    assert response.get_json()["category"] == "rover"
    assert response.get_json()["school"] == "SMA 1"


def test_purge_student(admin):
    body = _create_via_admin(admin).get_json()
    user_id = body["userId"]
    assert admin.delete(f"/api/v1/student/{user_id}/purge").status_code == 204
    assert admin.get(f"/api/v1/student/{user_id}").status_code == 404


# --- import -----------------------------------------------------------


def test_import_template(admin):
    response = admin.get("/api/v1/student/import-template")
    assert response.status_code == 200
    assert "spreadsheetml" in response.content_type


def test_import_requires_file(admin):
    response = admin.post("/api/v1/student/import", data={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "file_required"}


def test_import_bulk_upsert(admin):
    rows = [
        ["Budi", "Santoso", "budi@example.test", "budi", "Siswa1234", "cub"],
        ["Siti", "Rani", "siti@example.test", "siti", "Siswa1234", "scout"],
    ]
    buffer = build_xlsx(rows)
    response = admin.post(
        "/api/v1/student/import",
        data={"file": (buffer, "students.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.get_json() == {"inserted": 2, "updated": 0, "errors": []}

    buffer = build_xlsx(rows)
    again = admin.post(
        "/api/v1/student/import",
        data={"file": (buffer, "students.xlsx")},
        content_type="multipart/form-data",
    )
    assert again.get_json() == {"inserted": 0, "updated": 2, "errors": []}


def test_import_row_errors(admin):
    _create_via_admin(admin)
    rows = [
        ["Budi", "Santoso", "siti@example.test", "budi-x", "Siswa1234", "cub"],
        ["Bad", "Category", "bad@example.test", "bad", "Siswa1234", "invalid"],
    ]
    buffer = build_xlsx(rows)
    response = admin.post(
        "/api/v1/student/import",
        data={"file": (buffer, "students.xlsx")},
        content_type="multipart/form-data",
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["inserted"] == 0
    assert body["updated"] == 0
    messages = {e["message"] for e in body["errors"]}
    assert "email_already_registered" in messages
    assert any(m.startswith("validation:") for m in messages)


def test_import_does_not_convert_staff_user(admin):
    admin.post(
        "/api/v1/account/users",
        json={"email": "staff@example.com", "password": "S3cret!pass", "fullName": "Staff User"},
    )
    rows = [["Staff", "User", "staff@example.com", "staff@example.com", "Siswa1234", "cub"]]
    buffer = build_xlsx(rows)
    response = admin.post(
        "/api/v1/student/import",
        data={"file": (buffer, "students.xlsx")},
        content_type="multipart/form-data",
    )
    body = response.get_json()
    assert body["inserted"] == 0
    assert body["errors"][0]["message"] == "username_already_registered"

    from app.auth.models import User
    from app.student.models import Student
    from framework.extensions import db
    with admin.application.app_context():
        staff = db.session.query(User).filter_by(email="staff@example.com").one()
        assert db.session.get(Student, staff.id) is None
