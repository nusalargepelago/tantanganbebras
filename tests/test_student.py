from io import BytesIO

from conftest import (
    TEST_CITY_ID,
    TEST_SCHOOL_ID,
    TEST_SCHOOL_NAME,
    TEST_SCHOOL_SD_ID,
    TEST_SCHOOL_SD_NAME,
    csrf_client,
)
from openpyxl import Workbook

REGISTER = {
    "firstName": "Budi",
    "lastName": "Santoso",
    "email": "budi@example.test",
    "username": "budi",
    "password": "Siswa!234",
    "category": "cub",
    "schoolId": TEST_SCHOOL_ID,
}


def register_student(client, **overrides):
    payload = dict(REGISTER, **overrides)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": payload["email"],
            "username": payload["username"],
            "password": payload["password"],
            "fullName": f"{payload['firstName']} {payload['lastName']}",
        },
    )
    if response.status_code != 201:
        return response
    return client.post(
        "/api/v1/onboarding/student",
        json={
            "firstName": payload["firstName"],
            "lastName": payload["lastName"],
            "category": payload["category"],
            "schoolId": payload.get("schoolId", TEST_SCHOOL_ID),
        },
    )


def build_xlsx(rows, headers=None):
    if headers is None:
        headers = ["first_name", "last_name", "email", "username", "password",
                   "category", "school", "status"]
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "student"
    sheet.append(headers)
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
    assert body["registerUrl"] == "/register"


def test_student_register_endpoint_is_gone(client):
    response = client.post("/api/v1/student/auth/register", json={"username": "ghost"})
    assert response.status_code in (404, 405)


def test_register_creates_inactive_student(client):
    response = register_student(client)
    assert response.status_code == 201
    assert response.get_json() == {"classification": "student"}

    me = client.get("/api/v1/student/auth/me")
    assert me.status_code == 200
    body = me.get_json()
    assert body["student"]["status"] == "Inactive"
    assert body["student"]["category"] == "cub"
    assert body["student"]["city"] == "Kota Mataram"
    assert body["student"]["country"] == "Indonesia"


def test_register_duplicate_username(client):
    register_student(client)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.test",
            "username": "budi",
            "password": "Siswa!234",
            "fullName": "Other User",
        },
    )
    assert response.status_code == 409
    assert response.get_json() == {"message": "username_taken"}


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
    created = register_student(student_client)
    assert created.status_code == 201
    me = student_client.get("/api/v1/student/auth/me").get_json()
    user_id = me["student"]["userId"]

    assert admin.delete(f"/api/v1/student/{user_id}").status_code == 204

    fresh = csrf_client(admin.application)
    response = fresh.post(
        "/api/v1/student/auth/login",
        json={"username": "budi", "password": "Siswa!234"},
    )
    assert response.status_code == 401
    assert response.get_json() == {"message": "invalid_credentials"}


def test_login_accepts_student_account_via_staff_login(client):
    register_student(client)

    fresh = csrf_client(client.application)
    response = fresh.post(
        "/api/v1/auth/login",
        json={"identifier": "budi", "password": "Siswa!234"},
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
        "username": "siti", "password": "Siswa!234", "category": "scout",
        "schoolId": TEST_SCHOOL_ID,
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
        json={"category": "rover", "schoolId": TEST_SCHOOL_SD_ID},
    )
    assert response.status_code == 200
    assert response.get_json()["category"] == "rover"
    assert response.get_json()["school"] == TEST_SCHOOL_SD_NAME


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
        ["Budi", "Santoso", "budi@example.test", "budi", "Siswa!234", "cub", "SMPN 4 Gerung"],
        ["Siti", "Rani", "siti@example.test", "siti", "Siswa!234", "scout", "SMP Katolik Kesuma Mataram"],
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
        ["Budi", "Santoso", "siti@example.test", "budi-x", "Siswa!234", "cub",
         "SMPN 4 Gerung"],
        ["Bad", "Category", "bad@example.test", "bad", "Siswa!234", "invalid",
         "SMPN 4 Gerung"],
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
        json={
            "email": "staff@example.com",
            "username": "staffuser",
            "password": "S3cret!pass",
            "fullName": "Staff User",
        },
    )
    rows = [["Staff", "User", "staff@example.com", "staffuser", "Siswa!234", "cub",
             "SMPN 4 Gerung"]]
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


# --- teacher (school-scoped student management) --------------------------


def _create_via_teacher(teacher, **overrides):
    payload = {
        "firstName": "Dewi", "lastName": "Lestari", "email": "dewi@example.test",
        "username": "dewi", "password": "Siswa!234", "category": "cub",
    }
    payload.update(overrides)
    return teacher.post("/api/v1/student", json=payload)


def test_teacher_create_defaults_to_own_school_inactive(teacher):
    response = _create_via_teacher(teacher)
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert body["status"] == "Inactive"
    assert body["school"] == TEST_SCHOOL_NAME


def test_teacher_create_ignores_foreign_school_and_status(teacher):
    response = _create_via_teacher(
        teacher, schoolId=TEST_SCHOOL_SD_ID, status="Active",
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert body["school"] == TEST_SCHOOL_NAME
    assert body["status"] == "Inactive"


def test_staff_create_requires_school_id(member):
    response = member.post(
        "/api/v1/student",
        json={
            "firstName": "Dewi", "lastName": "Lestari", "email": "dewi@example.test",
            "username": "dewi", "password": "Siswa!234", "category": "cub",
        },
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "school_id_required"}


def test_teacher_list_scoped_to_own_school(admin, teacher):
    _create_via_admin(admin)
    _create_via_admin(
        admin, username="ranti", email="ranti@example.test",
        schoolId=TEST_SCHOOL_SD_ID,
    )

    body = teacher.get("/api/v1/student").get_json()
    assert body["total"] == 1
    assert [s["username"] for s in body["items"]] == ["siti"]

    body = teacher.get("/api/v1/student", query_string={"q": "ranti"}).get_json()
    assert body["total"] == 0


def test_teacher_get_foreign_student_is_404(admin, teacher):
    created = _create_via_admin(
        admin, username="ranti", email="ranti@example.test",
        schoolId=TEST_SCHOOL_SD_ID,
    ).get_json()
    response = teacher.get(f"/api/v1/student/{created['userId']}")
    assert response.status_code == 404
    assert response.get_json() == {"message": "student_not_found"}


def test_teacher_update_own_school(teacher):
    created = _create_via_teacher(teacher).get_json()
    response = teacher.patch(
        f"/api/v1/student/{created['userId']}", json={"category": "rover"},
    )
    assert response.status_code == 200
    assert response.get_json()["category"] == "rover"


def test_teacher_update_foreign_student_is_404(admin, teacher):
    created = _create_via_admin(
        admin, username="ranti", email="ranti@example.test",
        schoolId=TEST_SCHOOL_SD_ID,
    ).get_json()
    response = teacher.patch(
        f"/api/v1/student/{created['userId']}", json={"category": "rover"},
    )
    assert response.status_code == 404
    assert response.get_json() == {"message": "student_not_found"}


def test_teacher_update_identical_school_id_ok(teacher):
    created = _create_via_teacher(teacher).get_json()
    response = teacher.patch(
        f"/api/v1/student/{created['userId']}", json={"schoolId": TEST_SCHOOL_ID},
    )
    assert response.status_code == 200


def test_teacher_update_foreign_school_id_is_422(teacher):
    created = _create_via_teacher(teacher).get_json()
    response = teacher.patch(
        f"/api/v1/student/{created['userId']}", json={"schoolId": TEST_SCHOOL_SD_ID},
    )
    assert response.status_code == 422
    assert response.get_json() == {"message": "school_change_not_allowed"}


def test_teacher_update_status_is_422(teacher):
    created = _create_via_teacher(teacher).get_json()
    response = teacher.patch(
        f"/api/v1/student/{created['userId']}", json={"status": "Active"},
    )
    assert response.status_code == 422
    assert response.get_json() == {"message": "status_change_not_allowed"}


def test_teacher_activate_own_school(teacher):
    created = _create_via_teacher(teacher).get_json()
    response = teacher.post(f"/api/v1/student/{created['userId']}/activate")
    assert response.status_code == 200
    assert response.get_json()["status"] == "Active"


def test_teacher_activate_foreign_student_is_404(admin, teacher):
    created = _create_via_admin(
        admin, username="ranti", email="ranti@example.test",
        schoolId=TEST_SCHOOL_SD_ID,
    ).get_json()
    response = teacher.post(f"/api/v1/student/{created['userId']}/activate")
    assert response.status_code == 404
    assert response.get_json() == {"message": "student_not_found"}


def test_teacher_delete_restore_purge_forbidden(teacher):
    created = _create_via_teacher(teacher).get_json()
    user_id = created["userId"]
    assert teacher.delete(f"/api/v1/student/{user_id}").status_code == 403
    assert teacher.post(f"/api/v1/student/{user_id}/restore").status_code == 403
    assert teacher.delete(f"/api/v1/student/{user_id}/purge").status_code == 403


def test_teacher_import_template_omits_school_column(teacher):
    from openpyxl import load_workbook

    response = teacher.get("/api/v1/student/import-template")
    assert response.status_code == 200
    workbook = load_workbook(BytesIO(response.data))
    headers = [cell.value for cell in workbook.active[1]]
    assert "school" not in headers
    assert "status" in headers


def test_teacher_import_forces_school_and_inactive(admin, teacher):
    headers = ["first_name", "last_name", "email", "username", "password", "category"]
    rows = [["Dewi", "Lestari", "dewi@example.test", "dewi", "Siswa!234", "cub"]]
    buffer = build_xlsx(rows, headers=headers)
    response = teacher.post(
        "/api/v1/student/import",
        data={"file": (buffer, "students.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json() == {"inserted": 1, "updated": 0, "errors": []}

    listed = admin.get("/api/v1/student", query_string={"q": "dewi"}).get_json()
    assert listed["items"][0]["school"] == TEST_SCHOOL_NAME
    assert listed["items"][0]["status"] == "Inactive"


def test_teacher_import_school_and_status_columns_are_ignored(admin, teacher):
    rows = [["Dewi", "Lestari", "dewi@example.test", "dewi", "Siswa!234", "cub",
             "SD Negeri 8 Sokong", "Active"]]
    buffer = build_xlsx(rows)
    response = teacher.post(
        "/api/v1/student/import",
        data={"file": (buffer, "students.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json() == {"inserted": 1, "updated": 0, "errors": []}

    listed = admin.get("/api/v1/student", query_string={"q": "dewi"}).get_json()
    assert listed["items"][0]["school"] == TEST_SCHOOL_NAME
    assert listed["items"][0]["status"] == "Inactive"


def test_teacher_import_upsert_foreign_student_rejected(admin, teacher):
    _create_via_admin(
        admin, username="ranti", email="ranti@example.test",
        schoolId=TEST_SCHOOL_SD_ID, firstName="Ranti",
    ).get_json()
    rows = [["Hacked", "Name", "ranti@example.test", "ranti", "Siswa!234", "cub",
             TEST_SCHOOL_NAME, "Active"]]
    buffer = build_xlsx(rows)
    response = teacher.post(
        "/api/v1/student/import",
        data={"file": (buffer, "students.xlsx")},
        content_type="multipart/form-data",
    )
    body = response.get_json()
    assert body["inserted"] == 0
    assert body["updated"] == 0
    assert body["errors"] == [{"row": 2, "message": "student_outside_school"}]

    listed = admin.get("/api/v1/student", query_string={"q": "ranti"}).get_json()
    assert listed["items"][0]["firstName"] == "Ranti"
    assert listed["items"][0]["school"] == TEST_SCHOOL_SD_NAME


# --- inactive schools are not selectable (422 school_inactive) ----------


def _make_inactive_school(admin, name):
    created = admin.post("/api/v1/school", json={"name": name, "cityId": TEST_CITY_ID})
    assert created.status_code == 201
    school_id = created.get_json()["id"]
    deactivated = admin.patch(f"/api/v1/school/{school_id}", json={"isActive": False})
    assert deactivated.status_code == 200
    return school_id


def test_create_student_rejects_inactive_school(admin):
    school_id = _make_inactive_school(admin, "SMP Mati")
    payload = {
        "firstName": "Andi", "lastName": "Pratama", "email": "andi@example.test",
        "username": "andi", "password": "Siswa!234", "category": "cub",
        "schoolId": school_id,
    }
    response = admin.post("/api/v1/student", json=payload)
    assert response.status_code == 422
    assert response.get_json() == {"message": "school_inactive"}


def test_update_student_rejects_inactive_school(admin):
    body = _create_via_admin(admin).get_json()
    user_id = body["userId"]
    school_id = _make_inactive_school(admin, "SMP Mati 2")

    rejected = admin.patch(f"/api/v1/student/{user_id}", json={"schoolId": school_id})
    assert rejected.status_code == 422
    assert rejected.get_json() == {"message": "school_inactive"}

    # Unrelated field edits stay possible for a student whose school
    # was deactivated in the meantime (full-form payloads tolerated).
    admin.patch(f"/api/v1/school/{TEST_SCHOOL_ID}", json={"isActive": False})
    try:
        edited = admin.patch(f"/api/v1/student/{user_id}", json={"category": "rover", "schoolId": TEST_SCHOOL_ID})
        assert edited.status_code == 200
        assert edited.get_json()["category"] == "rover"
    finally:
        admin.patch(f"/api/v1/school/{TEST_SCHOOL_ID}", json={"isActive": True})


def test_onboarding_student_rejects_inactive_school(client, admin):
    school_id = _make_inactive_school(admin, "SMP Mati 3")
    response = register_student(
        client, username="nati", email="nati@example.test", schoolId=school_id,
    )
    assert response.status_code == 422
    assert response.get_json() == {"message": "school_inactive"}


def test_import_rows_reject_inactive_school(admin):
    school_name = "SMP Mati Import"
    school_id = _make_inactive_school(admin, school_name)
    assert school_id

    rows = [["Citra", "Sari", "citra@example.test", "citra", "Siswa!234", "cub",
             school_name, "Active"]]
    buffer = build_xlsx(rows)
    response = admin.post(
        "/api/v1/student/import",
        data={"file": (buffer, "students.xlsx")},
        content_type="multipart/form-data",
    )
    body = response.get_json()
    assert body["inserted"] == 0
    assert body["errors"] == [{"row": 2, "message": "school_inactive"}]


def test_student_presenter_exposes_school_id(admin):
    created = _create_via_admin(admin).get_json()
    assert created["schoolId"] == TEST_SCHOOL_ID
    fetched = admin.get(f"/api/v1/student/{created['userId']}").get_json()
    assert fetched["schoolId"] == TEST_SCHOOL_ID
