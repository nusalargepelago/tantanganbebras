from datetime import UTC, datetime, timedelta

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


def _make_questions(admin, codes=("Q000", "Q001"), **overrides):
    names = []
    for code in codes:
        payload = {
            **MC,
            "questionCode": code,
            "question": f"{code}?",
            "description": f"Context {code}",
            **overrides,
        }
        response = admin.post("/api/v1/question", json=payload)
        assert response.status_code == 201, response.get_json()
        names.append(response.get_json()["name"])
    return names


def _student(app, **overrides):
    client = csrf_client(app)
    response = client.post(
        "/api/v1/student/auth/register", json={**STUDENT, **overrides}
    )
    assert response.status_code == 201, response.get_json()
    return client


def _event_payload(question_names, **overrides):
    payload = {
        "eventName": "Bebras 2026",
        "eventDeadline": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "category": "cub",
        "timeLimit": 60,
        "questionsId": question_names,
        "published": True,
    }
    payload.update(overrides)
    return payload


def _create_event(admin, question_names, **overrides):
    response = admin.post("/api/v1/event", json=_event_payload(question_names, **overrides))
    return response


# --- admin CRUD -------------------------------------------------------


def test_create_event(admin):
    q = _make_questions(admin)
    response = _create_event(admin, q)
    assert response.status_code == 201
    body = response.get_json()
    assert body["eventName"] == "Bebras 2026"
    assert body["questionCount"] == len(q)
    assert body["published"] is True
    assert body["eventDeadline"].endswith("+00:00")


def test_create_rejects_invalid_category(admin):
    q = _make_questions(admin)
    response = _create_event(admin, q, category="elementary")
    assert response.status_code == 400
    assert response.get_json() == {"message": "category_invalid"}


def test_create_missing_question(admin):
    response = _create_event(admin, ["ghost-question"])
    assert response.status_code == 409
    assert response.get_json()["message"].startswith("question_not_found:")


def test_create_question_category_mismatch(admin):
    cub = _make_questions(admin)
    scout = _make_questions(admin, codes=("S000",), category="scout")
    response = _create_event(admin, cub + scout, category="cub")
    assert response.status_code == 409
    assert response.get_json()["message"].startswith("question_category_mismatch:")


def test_create_disabled_question(admin):
    q = _make_questions(admin)
    admin.delete(f"/api/v1/question/{q[0]}")
    response = _create_event(admin, q)
    assert response.status_code == 409
    assert response.get_json()["message"].startswith("question_disabled:")


def test_create_empty_questions(admin):
    response = _create_event(admin, [])
    assert response.status_code == 400
    assert response.get_json() == {"message": "questions_id_list_required"}


def test_list_events_requires_staff(app, admin):
    q = _make_questions(admin)
    _create_event(admin, q)
    body = admin.get("/api/v1/event").get_json()
    assert set(body) == {"items", "total", "page", "perPage"}
    assert body["total"] == 1

    student = _student(app)
    assert student.get("/api/v1/event").status_code == 403


def test_get_event_detail(admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    body = admin.get(f"/api/v1/event/{created['name']}").get_json()
    assert len(body["questions"]) == len(q)
    assert {x["name"] for x in body["questions"]} == set(q)


def test_update_event(admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    response = admin.patch(
        f"/api/v1/event/{created['name']}",
        json={"timeLimit": 30, "published": False},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["timeLimit"] == 30
    assert body["published"] is False


def test_update_missing_is_409(admin):
    response = admin.patch("/api/v1/event/ghost", json={"timeLimit": 30})
    assert response.status_code == 409
    assert response.get_json() == {"message": "event_not_found"}


def test_update_ignores_null_non_nullable(admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    response = admin.patch(
        f"/api/v1/event/{created['name']}",
        json={"category": None, "questionsId": q},
    )
    assert response.status_code == 200
    assert response.get_json()["category"] == "cub"


def test_soft_delete_restore_purge(admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    name = created["name"]

    assert admin.delete(f"/api/v1/event/{name}").status_code == 204
    assert admin.get("/api/v1/event").get_json()["total"] == 0

    restored = admin.post(f"/api/v1/event/{name}/restore")
    assert restored.status_code == 200
    assert admin.get("/api/v1/event").get_json()["total"] == 1

    assert admin.delete(f"/api/v1/event/{name}/purge").status_code == 204
    assert admin.get(f"/api/v1/event/{name}").status_code == 404


def test_results_empty_for_unknown(admin):
    body = admin.get("/api/v1/event/ghost/results").get_json()
    assert body == {"items": []}


# --- student attempts -------------------------------------------------


def test_make_attempt_idempotent(app, admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    student = _student(app)

    first = student.post(f"/api/v1/student/event/make/{created['name']}")
    assert first.status_code == 201
    second = student.post(f"/api/v1/student/event/make/{created['name']}")
    assert second.status_code == 201
    assert second.get_json()["name"] == first.get_json()["name"]


def test_make_guards(app, admin):
    q = _make_questions(admin)
    draft = _create_event(admin, q, published=False).get_json()
    student = _student(app)
    response = student.post(f"/api/v1/student/event/make/{draft['name']}")
    assert response.status_code == 409
    assert response.get_json() == {"message": "event_not_published"}

    expired = _create_event(
        admin, q, eventDeadline=(datetime.now(UTC) - timedelta(days=1)).isoformat()
    ).get_json()
    response = student.post(f"/api/v1/student/event/make/{expired['name']}")
    assert response.status_code == 409
    assert response.get_json() == {"message": "event_expired"}


def test_candidates(app, admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    student = _student(app)

    before = student.get("/api/v1/student/event").get_json()
    assert before["items"][0]["alreadyAttempted"] is False
    assert before["items"][0]["categoryMatch"] is True

    student.post(f"/api/v1/student/event/make/{created['name']}")
    after = student.get("/api/v1/student/event").get_json()
    assert after["items"][0]["alreadyAttempted"] is True


def test_start_returns_event_question_ids(app, admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    student = _student(app)
    attempt = student.post(f"/api/v1/student/event/make/{created['name']}").get_json()

    body = student.get(f"/api/v1/student/event/start/{attempt['name']}").get_json()
    assert body["eventStudent"]["name"] == attempt["name"]
    assert len(body["questions"]) == len(q)
    assert all(x["eventQuestionId"] for x in body["questions"])
    assert all(x["question"]["description"] for x in body["questions"])
    assert body["savedAnswers"] == []


def test_make_test_attempt_works_on_draft_event(admin):
    q = _make_questions(admin)
    draft = _create_event(admin, q, published=False).get_json()

    response = admin.post(f"/api/v1/student/event/make/{draft['name']}?test=1")
    assert response.status_code == 201
    attempt_name = response.get_json()["name"]
    assert attempt_name.startswith("test-")

    body = admin.get(f"/api/v1/student/event/start/{attempt_name}").get_json()
    assert len(body["questions"]) == len(q)

    results = admin.get(f"/api/v1/event/{draft['name']}/results").get_json()
    assert results == {"items": []}


def test_make_test_attempt_forbidden_for_student(app, admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    student = _student(app)

    response = student.post(f"/api/v1/student/event/make/{created['name']}?test=1")
    assert response.status_code == 403
    assert response.get_json() == {"message": "test_requires_staff"}


def test_test_attempt_does_not_shadow_real_attempt(admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()

    real = admin.post(f"/api/v1/student/event/make/{created['name']}").get_json()
    test_resp = admin.post(f"/api/v1/student/event/make/{created['name']}?test=1")
    print("TEST-RESP:", test_resp.status_code, repr(test_resp.get_data(as_text=True)))
    assert test_resp.status_code == 201, test_resp.get_data(as_text=True)
    test_attempt = test_resp.get_json()
    assert test_attempt["name"].startswith("test-")
    assert test_attempt["name"] != real["name"]

    again = admin.post(f"/api/v1/student/event/make/{created['name']}").get_json()
    assert again["name"] == real["name"]

    results = admin.get(f"/api/v1/event/{created['name']}/results").get_json()
    names = [row["name"] for row in results["items"]]
    assert real["name"] in names
    assert test_attempt["name"] not in names


def test_replacing_test_attempt_leaves_no_orphan_rows(app, admin):
    from app.event.models import (
        EventAttempt,
        EventAttemptAnswer,
        EventAttemptAnswerTemp,
    )
    from framework.extensions import db

    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    attempt = admin.post(
        f"/api/v1/student/event/make/{created['name']}?test=1"
    ).get_json()

    started = admin.get(f"/api/v1/student/event/start/{attempt['name']}").get_json()
    questions = started["questions"]

    autosaved = admin.post(
        "/api/v1/student/event/answer-temp",
        json={
            "eventStudentName": attempt["name"],
            "eventQuestionId": questions[0]["eventQuestionId"],
            "answer": "a",
        },
    )
    assert autosaved.status_code == 200, autosaved.get_json()

    submitted = admin.post(
        "/api/v1/student/event/store",
        json={
            "eventStudentName": attempt["name"],
            "answers": [
                {"eventQuestionId": row["eventQuestionId"], "answer": "a"}
                for row in questions
            ],
        },
    )
    assert submitted.status_code == 200, submitted.get_json()

    with app.app_context():
        assert db.session.query(EventAttemptAnswer).count() == len(questions)
        assert db.session.query(EventAttemptAnswerTemp).count() == 1

    replaced = admin.post(f"/api/v1/student/event/make/{created['name']}?test=1")
    assert replaced.status_code == 201, replaced.get_json()

    with app.app_context():
        assert db.session.query(EventAttemptAnswer).count() == 0
        assert db.session.query(EventAttemptAnswerTemp).count() == 0
        assert (
            db.session.query(EventAttempt)
            .filter(EventAttempt.name.like("test-%"))
            .count()
        ) == 1


def test_snapshot_survives_event_edit(app, admin):
    q = _make_questions(admin, codes=("Q000", "Q001"))
    extra = _make_questions(admin, codes=("Q002",))
    created = _create_event(admin, q).get_json()
    student = _student(app)
    attempt = student.post(f"/api/v1/student/event/make/{created['name']}").get_json()

    before = student.get(f"/api/v1/student/event/start/{attempt['name']}").get_json()
    before_names = {x["question"]["name"] for x in before["questions"]}

    admin.patch(
        f"/api/v1/event/{created['name']}", json={"questionsId": extra}
    )

    after = student.get(f"/api/v1/student/event/start/{attempt['name']}").get_json()
    after_names = {x["question"]["name"] for x in after["questions"]}
    assert after_names == before_names
    assert extra[0] not in after_names


def test_answer_temp_and_submit(app, admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    student = _student(app)
    attempt = student.post(f"/api/v1/student/event/make/{created['name']}").get_json()
    start = student.get(f"/api/v1/student/event/start/{attempt['name']}").get_json()
    first_qid = start["questions"][0]["eventQuestionId"]

    temp = student.post(
        "/api/v1/student/event/answer-temp",
        json={"eventStudentName": attempt["name"], "eventQuestionId": first_qid, "answer": "a"},
    )
    assert temp.status_code == 200
    assert temp.get_json() == {"notEmpty": True}

    answers = [
        {"eventQuestionId": x["eventQuestionId"], "answer": "a"} for x in start["questions"]
    ]
    submitted = student.post(
        "/api/v1/student/event/store",
        json={"eventStudentName": attempt["name"], "answers": answers},
    )
    assert submitted.status_code == 200
    assert submitted.get_json()["score"] == 20  # 2 questions x 10

    again = student.post(
        "/api/v1/student/event/store",
        json={"eventStudentName": attempt["name"], "answers": answers},
    )
    assert again.status_code == 409
    assert again.get_json() == {"message": "attempt_already_submitted"}


def test_result_owner_and_admin_results(app, admin):
    q = _make_questions(admin)
    created = _create_event(admin, q).get_json()
    student = _student(app)
    attempt = student.post(f"/api/v1/student/event/make/{created['name']}").get_json()
    start = student.get(f"/api/v1/student/event/start/{attempt['name']}").get_json()
    answers = [
        {"eventQuestionId": x["eventQuestionId"], "answer": "a"} for x in start["questions"]
    ]
    student.post(
        "/api/v1/student/event/store",
        json={"eventStudentName": attempt["name"], "answers": answers},
    )

    result = student.get(f"/api/v1/student/event/{attempt['name']}").get_json()
    assert result["score"] == 20

    results = admin.get(f"/api/v1/event/{created['name']}/results").get_json()
    assert len(results["items"]) == 1
    assert results["items"][0]["score"] == 20
