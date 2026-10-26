from conftest import csrf_client

MC = {
    "questionType": "Multiple Choice",
    "optionA": "Right",
    "optionB": "Wrong1",
    "optionC": "Wrong2",
    "optionD": "Wrong3",
    "correctAnswer": "a",
    "category": "cub",
    "difficultyLevel": "Easy",
    "status": "Active",
}

STUDENT = {
    "firstName": "Budi",
    "lastName": "Santoso",
    "email": "budi@example.test",
    "username": "budi",
    "password": "Siswa1234",
    "category": "cub",
}


def _make_questions(admin, n=10, **overrides):
    for i in range(n):
        payload = {
            **MC,
            "questionCode": f"Q{i:03d}",
            "question": f"Question {i}?",
            "description": f"Context {i}",
            **overrides,
        }
        response = admin.post("/api/v1/question", json=payload)
        assert response.status_code == 201, response.get_json()


def _student(app, **overrides):
    client = csrf_client(app)
    response = client.post(
        "/api/v1/student/auth/register", json={**STUDENT, **overrides}
    )
    assert response.status_code == 201, response.get_json()
    return client


def _create(client):
    response = client.post("/api/v1/student/practice/create")
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def _active_question_ids(client):
    body = client.get("/api/v1/student/practice/start").get_json()
    return [q["questionId"] for q in body["questions"]]


def test_create_requires_login(client):
    response = client.post("/api/v1/student/practice/create")
    assert response.status_code == 401
    assert response.get_json() == {"message": "unauthorized"}


def test_create_returns_sheet(app, admin):
    _make_questions(admin)
    student = _student(app)
    body = _create(student)
    assert body["name"].startswith("student-")
    assert body["category"] == "cub"
    assert body.get("score") is None
    assert body["startedAt"] is not None
    assert body.get("finishedAt") is None


def test_create_insufficient_pool(app, admin):
    student = _student(app, category="rover", email="r@example.test", username="rara")
    response = student.post("/api/v1/student/practice/create")
    assert response.status_code == 409
    assert response.get_json()["message"].startswith(
        "insufficient_question_in_category"
    )


def test_start_returns_questions_and_resume(app, admin):
    _make_questions(admin)
    student = _student(app)
    created = _create(student)
    body = student.get("/api/v1/student/practice/start").get_json()
    assert body["practice"]["name"] == created["name"]
    assert len(body["questions"]) == 10
    assert body["savedAnswers"] == []
    assert all(q["question"] is not None for q in body["questions"])
    assert all(q["question"]["description"] for q in body["questions"])


def test_start_without_practice_404(app, admin):
    _make_questions(admin)
    student = _student(app)
    response = student.get("/api/v1/student/practice/start")
    assert response.status_code == 404
    assert response.get_json() == {"message": "no_active_practice"}


def test_answer_temp_upsert(app, admin):
    _make_questions(admin)
    student = _student(app)
    _create(student)
    body = student.get("/api/v1/student/practice/start").get_json()
    name = body["practice"]["name"]
    qid = body["questions"][0]["questionId"]

    first = student.post(
        "/api/v1/student/practice/answer-temp",
        json={"practiceName": name, "questionId": qid, "answer": "a"},
    )
    assert first.status_code == 200
    assert first.get_json() == {"notEmpty": True}

    empty = student.post(
        "/api/v1/student/practice/answer-temp",
        json={"practiceName": name, "questionId": qid, "answer": ""},
    )
    assert empty.get_json() == {"notEmpty": False}


def test_answer_temp_validation(app, admin):
    _make_questions(admin)
    student = _student(app)
    missing = student.post("/api/v1/student/practice/answer-temp", json={"answer": "a"})
    assert missing.status_code == 400
    assert missing.get_json() == {
        "message": "value_must_specify_practice_or_event_student"
    }
    no_q = student.post(
        "/api/v1/student/practice/answer-temp", json={"practiceName": "p", "answer": "a"}
    )
    assert no_q.get_json() == {"message": "value_must_specify_question_id"}


def test_submit_scores_correctly(app, admin):
    _make_questions(admin)
    student = _student(app)
    _create(student)
    qids = _active_question_ids(student)
    name = student.get("/api/v1/student/practice/start").get_json()["practice"]["name"]

    answers = [{"questionId": q, "answer": "a"} for q in qids]
    response = student.post(
        "/api/v1/student/practice/store", json={"practiceName": name, "answers": answers}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["score"] == 100
    assert body["finishedAt"] is not None
    assert body["timeLimit"] is not None

    assert student.get("/api/v1/student/practice/start").status_code == 404


def test_submit_all_wrong_scores_zero(app, admin):
    _make_questions(admin)
    student = _student(app)
    _create(student)
    qids = _active_question_ids(student)
    name = student.get("/api/v1/student/practice/start").get_json()["practice"]["name"]

    answers = [{"questionId": q, "answer": "z"} for q in qids]
    response = student.post(
        "/api/v1/student/practice/store", json={"practiceName": name, "answers": answers}
    )
    assert response.get_json()["score"] == 0


def test_submit_twice_is_409(app, admin):
    _make_questions(admin)
    student = _student(app)
    _create(student)
    qids = _active_question_ids(student)
    name = student.get("/api/v1/student/practice/start").get_json()["practice"]["name"]
    answers = [{"questionId": q, "answer": "a"} for q in qids]
    student.post("/api/v1/student/practice/store", json={"practiceName": name, "answers": answers})

    again = student.post(
        "/api/v1/student/practice/store", json={"practiceName": name, "answers": answers}
    )
    assert again.status_code == 409
    assert again.get_json() == {"message": "practice_already_submitted"}


def test_answer_temp_after_submit_404(app, admin):
    _make_questions(admin)
    student = _student(app)
    _create(student)
    qids = _active_question_ids(student)
    name = student.get("/api/v1/student/practice/start").get_json()["practice"]["name"]
    answers = [{"questionId": q, "answer": "a"} for q in qids]
    student.post("/api/v1/student/practice/store", json={"practiceName": name, "answers": answers})

    response = student.post(
        "/api/v1/student/practice/answer-temp",
        json={"practiceName": name, "questionId": qids[0], "answer": "a"},
    )
    assert response.status_code == 404
    assert response.get_json() == {"message": "practice_already_submitted"}


def test_detail_owner_and_answers(app, admin):
    _make_questions(admin)
    student = _student(app)
    created = _create(student)
    qids = _active_question_ids(student)
    name = created["name"]
    answers = [
        {"questionId": qids[0], "answer": "a"},
        {"questionId": qids[1], "answer": "z"},
    ]
    student.post("/api/v1/student/practice/store", json={"practiceName": name, "answers": answers})

    body = student.get(f"/api/v1/student/practice/{name}").get_json()
    assert body["practice"]["name"] == name
    assert len(body["questions"]) == 10
    assert len(body["answers"]) == 10
    assert sum(1 for a in body["answers"] if a["isCorrect"]) == 1
    assert len(body["beforeShuffle"]) == 10


def test_detail_not_owned_404(app, admin):
    _make_questions(admin)
    owner = _student(app)
    created = _create(owner)
    other = _student(app, username="siti", email="siti@example.test")
    response = other.get(f"/api/v1/student/practice/{created['name']}")
    assert response.status_code == 404
    assert response.get_json() == {"message": "practice_not_found"}


def test_admin_detail_includes_student_and_shuffle(app, admin):
    _make_questions(admin)
    student = _student(app)
    created = _create(student)
    body = admin.get(f"/api/v1/practice/{created['name']}").get_json()
    assert body["student"]["username"] == "budi"
    assert len(body["beforeShuffle"]) == 10
    assert len(body["afterShuffle"]) == 10
    assert [r["originalIdx"] for r in body["beforeShuffle"]] == list(range(10))
    assert [r["shuffledIdx"] for r in body["afterShuffle"]] == list(range(10))


def test_admin_detail_exposes_options_and_answers(app, admin):
    _make_questions(admin)
    student = _student(app)
    created = _create(student)
    qids = _active_question_ids(student)
    student.post(
        "/api/v1/student/practice/store",
        json={
            "practiceName": created["name"],
            "answers": [{"questionId": qid, "answer": "a"} for qid in qids],
        },
    )

    body = admin.get(f"/api/v1/practice/{created['name']}").get_json()

    for section in ("beforeShuffle", "afterShuffle"):
        for row in body[section]:
            question = row["question"]
            assert question["questionType"] == "Multiple Choice"
            assert question["optionA"] and question["optionB"]
            assert question["optionC"] and question["optionD"]
            assert question["correctAnswer"] == "a"

    assert len(body["answers"]) == 10
    for row in body["answers"]:
        assert set(row) == {"questionId", "answer", "isCorrect"}
        assert row["answer"] == "a"
        assert row["isCorrect"] is True


def test_admin_detail_requires_staff(app, admin):
    _make_questions(admin)
    owner = _student(app)
    created = _create(owner)
    response = owner.get(f"/api/v1/practice/{created['name']}")
    assert response.status_code == 403


def test_mine_lists_practices(app, admin):
    _make_questions(admin)
    student = _student(app)
    _create(student)
    body = student.get("/api/v1/student/practice/mine").get_json()
    assert len(body["items"]) == 1


def test_admin_list_paginated_and_student_block(app, admin):
    _make_questions(admin)
    student = _student(app, school="SMP Negeri 1")
    _create(student)
    body = admin.get("/api/v1/practice").get_json()
    assert set(body) == {"items", "total", "page", "perPage"}
    assert body["total"] == 1
    assert body["items"][0]["studentName"] == "Budi Santoso"
    assert body["items"][0]["studentEmail"] == "budi@example.test"
    assert body["items"][0]["studentSchool"] == "SMP Negeri 1"

    assert student.get("/api/v1/practice").status_code == 403


def test_practice_admin_out_omits_student_name_when_missing():
    from app.practice.models import Practice
    from app.practice.presenters import PracticeAdminOut

    practice = Practice(name="orphan", student_id="missing", category="cub")
    assert "studentName" not in PracticeAdminOut.from_practice(practice).to_dict()
    with_name = PracticeAdminOut.from_practice(practice, student_name="A B").to_dict()
    assert with_name["studentName"] == "A B"


def test_practice_admin_out_omits_student_email_when_missing():
    from app.practice.models import Practice
    from app.practice.presenters import PracticeAdminOut

    practice = Practice(name="orphan", student_id="missing", category="cub")
    assert "studentEmail" not in PracticeAdminOut.from_practice(practice).to_dict()
    with_email = PracticeAdminOut.from_practice(
        practice, student_email="a@example.test"
    ).to_dict()
    assert with_email["studentEmail"] == "a@example.test"


def test_practice_admin_out_omits_student_school_when_missing():
    from app.practice.models import Practice
    from app.practice.presenters import PracticeAdminOut

    practice = Practice(name="orphan", student_id="missing", category="cub")
    assert "studentSchool" not in PracticeAdminOut.from_practice(practice).to_dict()
    with_school = PracticeAdminOut.from_practice(
        practice, student_school="SMP Negeri 1"
    ).to_dict()
    assert with_school["studentSchool"] == "SMP Negeri 1"


# --- practice settings -------------------------------------------------


def test_settings_min_questions_default(admin):
    body = admin.get("/api/v1/practice/settings").get_json()
    assert body == {"minQuestions": 10}


def test_settings_update_min_questions(admin):
    response = admin.put("/api/v1/practice/settings", json={"minQuestions": 3})
    assert response.status_code == 200
    assert response.get_json() == {"minQuestions": 3}
    assert admin.get("/api/v1/practice/settings").get_json() == {"minQuestions": 3}


def test_create_uses_configured_min_questions(app, admin):
    _make_questions(admin, n=3)
    admin.put("/api/v1/practice/settings", json={"minQuestions": 3})
    student = _student(app)
    created = _create(student)
    detail = admin.get(f"/api/v1/practice/{created['name']}").get_json()
    assert len(detail["beforeShuffle"]) == 3


def test_create_insufficient_pool_uses_configured_min(app, admin):
    _make_questions(admin, n=3)
    admin.put("/api/v1/practice/settings", json={"minQuestions": 5})
    student = _student(app)
    response = student.post("/api/v1/student/practice/create")
    assert response.status_code == 409
    assert response.get_json()["message"] == (
        "insufficient_question_in_category: have 3, need 5"
    )


def test_settings_require_auth_and_staff(app):
    student = _student(app)
    anon = csrf_client(app)

    assert anon.get("/api/v1/practice/settings").status_code == 401
    assert student.get("/api/v1/practice/settings").status_code == 403
    response = student.put("/api/v1/practice/settings", json={"minQuestions": 3})
    assert response.status_code == 403


def test_settings_update_rejects_invalid(admin):
    response = admin.put("/api/v1/practice/settings", json={"minQuestions": 0})
    assert response.status_code == 400


# --- test mode ----------------------------------------------------------


def test_create_test_practice_for_staff_without_student(app, admin):
    from app.practice.models import Practice
    from framework.extensions import db

    _make_questions(admin)
    response = admin.post("/api/v1/student/practice/create?test=1&category=cub")
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert body["name"].startswith("test-")
    assert body["category"] == "cub"

    started = admin.get("/api/v1/student/practice/start")
    assert started.status_code == 200
    payload = started.get_json()
    assert payload["practice"]["name"] == body["name"]
    assert len(payload["questions"]) == 10

    assert admin.get("/api/v1/student/practice/mine").get_json() == {"items": []}
    with app.app_context():
        assert db.session.query(Practice).count() == 1


def test_create_test_practice_requires_category(app, admin):
    _make_questions(admin)
    response = admin.post("/api/v1/student/practice/create?test=1")
    assert response.status_code == 400
    assert response.get_json() == {"message": "category_required"}


def test_create_test_practice_rejects_unknown_category(app, admin):
    _make_questions(admin)
    response = admin.post("/api/v1/student/practice/create?test=1&category=nope")
    assert response.status_code == 400
    assert response.get_json() == {"message": "category_invalid"}


def test_create_test_practice_forbidden_for_student(app, admin):
    _make_questions(admin)
    student = _student(app)
    response = student.post("/api/v1/student/practice/create?test=1&category=cub")
    assert response.status_code == 403
    assert response.get_json() == {"message": "test_requires_staff"}


def test_create_without_test_still_requires_student_row(admin):
    response = admin.post("/api/v1/student/practice/create")
    assert response.status_code == 409
    assert response.get_json() == {"message": "student_not_found"}


def test_repeated_test_practice_replaces_previous(app, admin):
    from app.practice.models import Practice, PracticeQuestion
    from framework.extensions import db

    _make_questions(admin)
    first = admin.post("/api/v1/student/practice/create?test=1&category=cub")
    second = admin.post("/api/v1/student/practice/create?test=1&category=cub")
    assert first.status_code == 201, first.get_json()
    assert second.status_code == 201, second.get_json()

    with app.app_context():
        assert db.session.query(Practice).count() == 1
        assert db.session.query(PracticeQuestion).count() == 10


def test_admin_list_hides_test_practices(app, admin):
    _make_questions(admin)
    response = admin.post("/api/v1/student/practice/create?test=1&category=cub")
    assert response.status_code == 201, response.get_json()

    body = admin.get("/api/v1/practice").get_json()
    assert body["total"] == 0


def test_start_returns_unfinished_practice_when_newest_is_finished(app, admin):
    from datetime import UTC, datetime, timedelta

    from app.auth.models import User
    from app.practice.models import Practice
    from framework.extensions import db

    _make_questions(admin)
    student = _student(app)
    current = _create(student)

    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == "budi"))
        db.session.add(
            Practice(
                name="stale-practice",
                student_id=user.id,
                category="cub",
                started_at=datetime.now(UTC) - timedelta(days=1),
                created_at=datetime.now(UTC) - timedelta(days=1),
            )
        )
        newest = db.session.query(Practice).filter_by(name=current["name"]).one()
        newest.finished_at = datetime.now(UTC)
        db.session.commit()

    payload = student.get("/api/v1/student/practice/start").get_json()
    assert payload["practice"]["name"] == "stale-practice"
