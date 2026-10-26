from conftest import csrf_client

STUDENT = {
    "firstName": "Budi",
    "lastName": "Santoso",
    "email": "budi@example.test",
    "username": "budi",
    "password": "Siswa1234",
    "category": "cub",
}


def _student(app, **overrides):
    client = csrf_client(app)
    response = client.post(
        "/api/v1/student/auth/register", json={**STUDENT, **overrides}
    )
    assert response.status_code == 201, response.get_json()
    return client


def test_admin_dashboard_shape(admin):
    body = admin.get("/api/v1/dashboard").get_json()
    assert set(body) == {"counts", "recentEvents", "recentStudents"}
    assert set(body["counts"]) == {
        "questionCub",
        "questionScout",
        "questionRover",
        "eventActive",
        "studentActive",
        "studentInactive",
        "eventStudentToday",
    }
    assert body["counts"]["questionCub"] == 0
    assert body["recentEvents"] == []
    assert body["recentStudents"] == []


def test_admin_dashboard_requires_staff(app, admin):
    student = _student(app)
    assert student.get("/api/v1/dashboard").status_code == 403


def test_admin_dashboard_requires_login(client):
    assert client.get("/api/v1/dashboard").status_code == 401


def test_admin_dashboard_stats_shape(admin):
    body = admin.get("/api/v1/dashboard/stats").get_json()
    assert set(body) == {"totals", "schools", "registrations", "categories"}
    assert set(body["totals"]) == {"students", "schools"}
    assert body["totals"] == {"students": 0, "schools": 0}
    assert body["schools"] == []
    assert body["registrations"] == []
    assert body["categories"] == []


def test_admin_dashboard_stats_requires_staff(app, admin):
    student = _student(app)
    assert student.get("/api/v1/dashboard/stats").status_code == 403


def test_admin_dashboard_stats_requires_login(client):
    assert client.get("/api/v1/dashboard/stats").status_code == 401


def test_admin_dashboard_stats_populated(app, admin):
    from datetime import UTC, datetime

    from app.student.models import Student
    from framework.extensions import db

    _student(
        app,
        email="stu1@example.test",
        username="stu1",
        school="SMA Negeri 1 Jakarta",
        category="cub",
    )
    _student(
        app,
        email="stu2@example.test",
        username="stu2",
        school="SMA Negeri 1 Jakarta",
        category="scout",
    )
    _student(app, email="stu3@example.test", username="stu3", category="cub")
    _student(app, email="stu4@example.test", username="stu4", school="", category="rover")

    with app.app_context():
        rows = {s.user.email: s for s in db.session.query(Student).all()}
        rows["stu1@example.test"].created_at = datetime(2025, 6, 1, tzinfo=UTC)
        rows["stu2@example.test"].created_at = datetime(2026, 1, 1, tzinfo=UTC)
        rows["stu3@example.test"].created_at = datetime(2026, 2, 1, tzinfo=UTC)
        rows["stu4@example.test"].created_at = datetime(2026, 3, 1, tzinfo=UTC)
        db.session.commit()

    body = admin.get("/api/v1/dashboard/stats").get_json()
    assert body["totals"] == {"students": 4, "schools": 1}
    # count ties break on label ASC; "(No school)" sorts before letters in ASCII
    assert body["schools"] == [
        {"school": "(No school)", "count": 2},
        {"school": "SMA Negeri 1 Jakarta", "count": 2},
    ]
    assert body["registrations"] == [
        {"year": 2025, "count": 1},
        {"year": 2026, "count": 3},
    ]
    assert body["categories"] == [
        {"category": "cub", "count": 2},
        {"category": "scout", "count": 1},
        {"category": "rover", "count": 1},
    ]


def test_student_dashboard(app):
    student = _student(app, category="scout")
    body = student.get("/api/v1/student/dashboard").get_json()
    assert body["category"] == "scout"
    assert body["totalPractice"] == 0
    assert body["totalChallenge"] == 0
    assert body["lastPractice"] is None
    assert body["lastEvent"] is None


def test_student_dashboard_404_without_student_row(admin):
    response = admin.get("/api/v1/student/dashboard")
    assert response.status_code == 404
    assert response.get_json() == {"message": "student_not_found"}

