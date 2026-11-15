"""School & city master data — admin CRUD and session-readable lists."""
from __future__ import annotations

from conftest import TEST_CITY_ID, TEST_CITY_SOKONG_ID, TEST_SCHOOL_ID, TEST_SCHOOL_NAME


def test_list_schools_session(member):
    body = member.get("/api/v1/school").get_json()
    assert "items" in body
    names = [item["name"] for item in body["items"]]
    assert TEST_SCHOOL_NAME in names
    assert len(names) == 30


def test_list_schools_requires_auth(client):
    assert client.get("/api/v1/school").status_code == 401


def test_list_cities_session(member):
    body = member.get("/api/v1/city").get_json()
    assert "items" in body
    assert len(body["items"]) == 514
    names = [item["name"] for item in body["items"]]
    assert "Kota Mataram" in names
    assert "Kabupaten Lombok Utara" in names
    assert "Kota Administrasi Jakarta Selatan" in names
    assert "Kabupaten Administrasi Kepulauan Seribu" in names


def test_list_cities_requires_auth(client):
    assert client.get("/api/v1/city").status_code == 401


# --- admin CRUD -----------------------------------------------------------


def test_admin_can_create_school(admin):
    created = admin.post(
        "/api/v1/school", json={"name": "SMP Negeri Baru", "cityId": TEST_CITY_ID}
    )
    assert created.status_code == 201
    assert created.get_json()["name"] == "SMP Negeri Baru"
    assert created.get_json()["isActive"] is True
    assert created.get_json()["city"] == {"id": TEST_CITY_ID, "name": "Kota Mataram"}

    renamed = admin.patch(f"/api/v1/school/{created.get_json()['id']}", json={"name": "SMPN Baru"})
    assert renamed.status_code == 200
    assert renamed.get_json()["name"] == "SMPN Baru"


def test_admin_create_requires_city(admin):
    assert admin.post("/api/v1/school", json={"name": "SMP Tanpa Kota"}).status_code == 400
    unknown = admin.post(
        "/api/v1/school",
        json={"name": "SMP Kota Ngawur", "cityId": "00000000-0000-4000-8000-0000000000ff"},
    )
    assert unknown.status_code == 400
    assert unknown.get_json() == {"message": "city_not_in_master"}


def test_admin_move_school_city(admin):
    created = admin.post(
        "/api/v1/school", json={"name": "SMP Pindah", "cityId": TEST_CITY_ID}
    ).get_json()
    moved = admin.patch(
        f"/api/v1/school/{created['id']}", json={"cityId": TEST_CITY_SOKONG_ID}
    )
    assert moved.status_code == 200
    assert moved.get_json()["city"]["name"] == "Kabupaten Lombok Utara"


def test_admin_create_duplicate(admin):
    assert (
        admin.post(
            "/api/v1/school", json={"name": TEST_SCHOOL_NAME, "cityId": TEST_CITY_ID}
        ).status_code
        == 409
    )
    assert (
        admin.post(
            "/api/v1/school",
            json={"name": "  " + TEST_SCHOOL_NAME + "  ", "cityId": TEST_CITY_ID},
        ).status_code
        == 409
    )
    assert (
        admin.post(
            "/api/v1/school", json={"name": "SMPN Baru", "cityId": TEST_CITY_ID}
        ).status_code
        == 201
    )
    assert (
        admin.post(
            "/api/v1/school",
            json={"name": "smp katolik kesuma mataram", "cityId": TEST_CITY_ID},
        ).status_code
        == 409
    )


def test_admin_create_validation(admin):
    assert admin.post("/api/v1/school", json={"name": "x"}).status_code == 400
    assert admin.post("/api/v1/school", json={}).status_code == 400


def test_patch_deactivate_and_reactivate(admin, member):
    school_id = TEST_SCHOOL_ID

    deactivated = admin.patch(f"/api/v1/school/{school_id}", json={"isActive": False})
    assert deactivated.status_code == 200
    assert deactivated.get_json()["isActive"] is False

    # A deactivated school disappears from the member-facing list...
    body = member.get("/api/v1/school").get_json()
    assert TEST_SCHOOL_NAME not in [i["name"] for i in body["items"]]
    # ...but is visible to admin with includeDisabled=1...
    body = admin.get("/api/v1/school", query_string={"includeDisabled": "1"}).get_json()
    assert any(i["name"] == TEST_SCHOOL_NAME for i in body["items"])

    reactivated = admin.patch(f"/api/v1/school/{school_id}", json={"isActive": True})
    assert reactivated.status_code == 200
    body = member.get("/api/v1/school").get_json()
    assert TEST_SCHOOL_NAME in [i["name"] for i in body["items"]]


def test_patch_unknown_school_is_404(admin):
    response = admin.patch("/api/v1/school/00000000-0000-4000-8000-0000000000ff", json={"name": "Xyz"})
    assert response.status_code == 404
    assert response.get_json() == {"message": "school_not_found"}


def test_non_admin_cannot_rename_or_deactivate_school(admin, member):
    created = admin.post(
        "/api/v1/school", json={"name": "SMPN Lainnya", "cityId": TEST_CITY_ID}
    ).get_json()
    assert member.patch(f"/api/v1/school/{created['id']}", json={"name": "Hack"}).status_code == 403
    assert member.patch(f"/api/v1/school/{created['id']}", json={"isActive": False}).status_code == 403


def test_onboarding_student_rejects_unknown_ids(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "newbie@example.test",
            "username": "newbie",
            "password": "Siswa!234",
            "fullName": "New Bie",
        },
    )
    response = client.post(
        "/api/v1/onboarding/student",
        json={"firstName": "New", "lastName": "Bie", "category": "cub", "schoolId": "nope"},
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "school_not_in_master"}


def test_classify_teacher_ignores_client_city(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "guru@example.test",
            "username": "guru",
            "password": "Siswa!234",
            "fullName": "Guru Baru",
        },
    )
    response = client.post(
        "/api/v1/onboarding/teacher",
        json={
            "firstName": "Guru",
            "lastName": "Baru",
            "schoolId": TEST_SCHOOL_ID,
            "cityId": "00000000-0000-4000-8000-0000000000ff",
        },
    )
    assert response.status_code == 201

    from app.auth.models import User
    from app.onboarding.models import Teacher
    from framework.extensions import db

    with client.application.app_context():
        user = db.session.query(User).filter_by(email="guru@example.test").one()
        teacher = db.session.get(Teacher, user.id)
        assert teacher is not None
        assert teacher.school.city.name == "Kota Mataram"


# --- non-admin school creation (duplicates rejected) ----------------------


def test_non_admin_can_create_new_school(app, member):
    from app.school.models import School
    from framework.extensions import db

    with app.app_context():
        db.session.query(School).delete()
        db.session.commit()

    created = member.post(
        "/api/v1/school", json={"name": "SMP Baru", "cityId": TEST_CITY_ID},
    )
    assert created.status_code == 201, created.get_json()
    body = created.get_json()
    assert body["name"] == "SMP Baru"
    assert body["city"] == {"id": TEST_CITY_ID, "name": "Kota Mataram"}

    # The master is non-empty now, but non-admins keep creating non-duplicates.
    second = member.post(
        "/api/v1/school", json={"name": "SMP Baru 2", "cityId": TEST_CITY_ID},
    )
    assert second.status_code == 201


def test_non_admin_can_create_with_active_master(member):
    response = member.post(
        "/api/v1/school", json={"name": "SMP Ditambahkan Member", "cityId": TEST_CITY_ID},
    )
    assert response.status_code == 201, response.get_json()


def test_non_admin_cannot_duplicate_active_school(member):
    response = member.post(
        "/api/v1/school", json={"name": TEST_SCHOOL_NAME, "cityId": TEST_CITY_ID},
    )
    assert response.status_code == 409
    assert response.get_json() == {"message": "school_already_exists"}


def test_non_admin_cannot_duplicate_active_school_normalized(member):
    padded = f"  {TEST_SCHOOL_NAME.lower()}  "
    response = member.post(
        "/api/v1/school", json={"name": padded, "cityId": TEST_CITY_ID},
    )
    assert response.status_code == 409
    assert response.get_json() == {"message": "school_already_exists"}


def test_admin_can_create_after_wiping_master(app, admin):
    from app.school.models import School
    from framework.extensions import db

    with app.app_context():
        db.session.query(School).delete()
        db.session.commit()

    for name in ("SMP Bootstrap", "SMP Bootstrap 2"):
        created = admin.post(
            "/api/v1/school", json={"name": name, "cityId": TEST_CITY_ID},
        )
        assert created.status_code == 201


def test_non_admin_can_create_when_only_inactive_schools_exist(app, member):
    from app.school.models import School
    from framework.extensions import db

    with app.app_context():
        db.session.query(School).delete()
        db.session.add(School(name="SMP Nonaktif", city_id=TEST_CITY_ID, is_active=False))
        db.session.commit()

    created = member.post(
        "/api/v1/school", json={"name": "SMP Baru", "cityId": TEST_CITY_ID},
    )
    assert created.status_code == 201, created.get_json()


def test_non_admin_duplicate_includes_inactive_schools(app, member):
    with app.app_context():
        from app.school.models import School
        from framework.extensions import db

        db.session.query(School).delete()
        # Inactive duplicate name with different casing/spacing.
        db.session.add(School(name="SMP  Bootstrap", city_id=TEST_CITY_ID, is_active=False))
        db.session.commit()

    created = member.post(
        "/api/v1/school", json={"name": "smp bootstrap", "cityId": TEST_CITY_ID},
    )
    assert created.status_code == 409
    assert created.get_json() == {"message": "school_already_exists"}
