from datetime import UTC, datetime

MC = {
    "questionCode": "TB-SGA-001",
    "question": "Which pattern comes next?",
    "questionType": "Multiple Choice",
    "optionA": "Option A",
    "optionB": "Option B",
    "optionC": "Option C",
    "optionD": "Option D",
    "correctAnswer": "a",
    "category": "cub",
    "difficultyLevel": "Easy",
    "status": "Active",
}

ESSAY = {
    "questionCode": "TB-SGA-002",
    "question": "Explain your reasoning.",
    "questionType": "Essay",
    "category": "cub",
    "referenceAnswer": "Because patterns repeat.",
}

IMG = '<img src="data:image/png;base64,iVBORw0KGgo=" alt="diagram">'


def _create(client, **overrides):
    return client.post("/api/v1/question", json={**MC, **overrides})


def test_list_requires_login(client):
    response = client.get("/api/v1/question")
    assert response.status_code == 401
    assert response.get_json() == {"message": "unauthorized"}


def test_option_list_shape(member):
    body = member.get("/api/v1/question/option-list").get_json()
    assert set(body) == {"category", "difficultyLevel", "questionType", "option", "status"}
    assert body["category"] == ["cub", "scout", "rover"]


def test_create_mc_question(member):
    response = _create(member)
    assert response.status_code == 201
    body = response.get_json()
    for key in (
        "name",
        "questionCode",
        "question",
        "questionType",
        "optionA",
        "optionB",
        "optionC",
        "optionD",
        "correctAnswer",
        "category",
        "difficultyLevel",
        "status",
        "creatorId",
        "disabled",
        "createdAt",
        "updatedAt",
    ):
        assert key in body
    assert body["name"] == "tb-sga-001"
    assert body["questionType"] == "Multiple Choice"
    assert body["correctAnswer"] == "a"
    assert body["disabled"] is False
    assert body["createdAt"].endswith("+00:00")
    assert "referenceAnswer" not in body
    assert "description" not in body
    assert "topicId" not in body
    assert "disabledAt" not in body


def test_create_with_description(member):
    response = _create(member, description="<p>Read the story.</p>")
    assert response.status_code == 201
    assert response.get_json()["description"] == "<p>Read the story.</p>"


def test_blank_description_is_omitted(member):
    response = _create(member, description="   ")
    assert response.status_code == 201
    assert "description" not in response.get_json()


def test_update_and_clear_description(member):
    created = _create(member).get_json()
    response = member.patch(
        f"/api/v1/question/{created['name']}",
        json={"description": "<p>Context</p>"},
    )
    assert response.status_code == 200
    assert response.get_json()["description"] == "<p>Context</p>"

    cleared = member.patch(
        f"/api/v1/question/{created['name']}", json={"description": None}
    )
    assert cleared.status_code == 200
    assert "description" not in cleared.get_json()


def test_blank_html_description_is_omitted(member):
    for blank in ("<p></p>", "<p>&nbsp;</p>", "<p><br></p>", "   "):
        response = _create(member, description=blank)
        assert response.status_code == 201
        assert "description" not in response.get_json()


def test_image_only_description_is_kept(member):
    response = _create(member, description=IMG)
    assert response.status_code == 201
    assert response.get_json()["description"] == IMG


def test_rich_option_html_round_trip(member):
    option_a = "<p><strong>1</strong> dan <em>2</em></p>"
    option_b = "<p>First<br>second</p><ul><li>bullet</li></ul>"
    response = _create(member, optionA=option_a, optionB=option_b, optionC=IMG)
    assert response.status_code == 201
    body = response.get_json()
    assert body["optionA"] == option_a
    assert body["optionB"] == option_b
    assert body["optionC"] == IMG


def test_update_keeps_untouched_legacy_option_html(member):
    legacy = '<p style="text-align:center">A</p>'
    created = _create(member, optionA=legacy).get_json()
    updated = member.patch(
        f"/api/v1/question/{created['name']}",
        json={"question": "<p>Updated prompt</p>"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["optionA"] == legacy


def test_mc_rejects_blank_html_options(member):
    for blank in ("<p></p>", "<p>&nbsp;</p>", "<p><br></p>", "   "):
        response = _create(member, optionB=blank)
        assert response.status_code == 400
        assert response.get_json() == {"message": "value_pg_requires_option_b"}


def test_image_only_option_is_valid(member):
    response = _create(member, optionD=IMG)
    assert response.status_code == 201
    assert response.get_json()["optionD"] == IMG


def test_blank_html_question_rejected(member):
    response = _create(member, question="<p>&nbsp;</p>")
    assert response.status_code == 400
    assert response.get_json() == {"message": "question_required"}


def test_essay_reference_blank_html_rejected(member):
    response = member.post(
        "/api/v1/question", json={**ESSAY, "referenceAnswer": "<p><br></p>"}
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_essay_requires_reference_answer"}


def test_create_essay_question(member):
    response = member.post("/api/v1/question", json=ESSAY)
    assert response.status_code == 201
    body = response.get_json()
    assert body["questionType"] == "Essay"
    assert body["referenceAnswer"] == "Because patterns repeat."
    assert "optionA" not in body
    assert "correctAnswer" not in body


def test_mc_requires_options_in_order(member):
    payload = {k: v for k, v in MC.items() if k != "optionB"}
    response = member.post("/api/v1/question", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_pg_requires_option_b"}


def test_mc_requires_correct_answer(member):
    payload = {k: v for k, v in MC.items() if k != "correctAnswer"}
    response = member.post("/api/v1/question", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_pg_requires_correct_answer"}


def test_essay_requires_reference_answer(member):
    payload = {k: v for k, v in ESSAY.items() if k != "referenceAnswer"}
    response = member.post("/api/v1/question", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_essay_requires_reference_answer"}


def test_rejects_invalid_category(member):
    response = _create(member, category="elementary")
    assert response.status_code == 400
    assert response.get_json() == {"message": "category_invalid"}


def test_rejects_invalid_correct_answer(member):
    response = _create(member, correctAnswer="z")
    assert response.status_code == 400
    assert response.get_json() == {"message": "correct_answer_must_be_a_b_c_or_d"}


def test_correct_answer_is_lowercased(member):
    response = _create(member, correctAnswer="B")
    assert response.status_code == 201
    assert response.get_json()["correctAnswer"] == "b"


def test_duplicate_code_gets_year_suffix(member):
    year = datetime.now(UTC).year
    first = _create(member).get_json()
    second = _create(member).get_json()
    assert first["name"] == "tb-sga-001"
    assert second["name"] == f"tb-sga-001-{year}-0001"


def test_create_with_unknown_topic(member):
    response = _create(member, topicId="no-such-topic")
    assert response.status_code == 404
    assert response.get_json() == {"message": "topic_not_found"}


def test_list_total_matches_filters(member):
    _create(member)
    _create(member, category="scout")
    body = member.get("/api/v1/question", query_string={"category": "cub"}).get_json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_list_search_q(member):
    _create(member)
    body = member.get("/api/v1/question", query_string={"q": "pattern"}).get_json()
    assert body["total"] == 1
    empty = member.get("/api/v1/question", query_string={"q": "zzz"}).get_json()
    assert empty["total"] == 0


def test_list_search_matches_description(member):
    _create(member, description="<p>uniqueword</p>")
    body = member.get("/api/v1/question", query_string={"q": "uniqueword"}).get_json()
    assert body["total"] == 1


def test_list_omits_description_but_detail_keeps_it(member):
    created = _create(member, description="<p>Read the story.</p>").get_json()
    listed = member.get("/api/v1/question").get_json()["items"][0]
    assert "description" not in listed

    detail = member.get(f"/api/v1/question/{created['name']}").get_json()
    assert detail["description"] == "<p>Read the story.</p>"


def test_list_filters_by_topic(member):
    topic = member.post(
        "/api/v1/topic", json={"title": "Linked", "category": "cub"}
    ).get_json()
    _create(member, topicId=topic["name"])
    body = member.get(
        "/api/v1/question", query_string={"topicId": topic["name"]}
    ).get_json()
    assert body["total"] == 1


def test_soft_delete_hides_from_list_but_detail_survives(member):
    created = _create(member).get_json()
    assert member.delete(f"/api/v1/question/{created['name']}").status_code == 204

    assert member.get("/api/v1/question").get_json()["total"] == 0
    included = member.get(
        "/api/v1/question", query_string={"includeDisabled": "true"}
    ).get_json()
    assert included["total"] == 1

    detail = member.get(f"/api/v1/question/{created['name']}").get_json()
    assert detail["disabled"] is True
    assert detail["disabledAt"].endswith("+00:00")


def test_restore_question(member):
    created = _create(member).get_json()
    member.delete(f"/api/v1/question/{created['name']}")
    response = member.post(f"/api/v1/question/{created['name']}/restore")
    assert response.status_code == 200
    assert response.get_json() == {"message": "restored"}
    assert member.get("/api/v1/question").get_json()["total"] == 1


def test_purge_question(member):
    created = _create(member).get_json()
    member.delete(f"/api/v1/question/{created['name']}")
    assert member.delete(f"/api/v1/question/{created['name']}/purge").status_code == 204
    assert member.get(f"/api/v1/question/{created['name']}").status_code == 404


def test_update_revalidates_type_transition(member):
    created = _create(member).get_json()
    response = member.patch(
        f"/api/v1/question/{created['name']}", json={"questionType": "Essay"}
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_essay_requires_reference_answer"}

    response = member.patch(
        f"/api/v1/question/{created['name']}",
        json={"questionType": "Essay", "referenceAnswer": "A reference."},
    )
    assert response.status_code == 200
    assert response.get_json()["questionType"] == "Essay"


def test_update_question_fields(member):
    created = _create(member).get_json()
    response = member.patch(
        f"/api/v1/question/{created['name']}",
        json={"question": "Updated body", "difficultyLevel": "Hard"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["question"] == "Updated body"
    assert body["difficultyLevel"] == "Hard"


def test_update_empty_body(member):
    created = _create(member).get_json()
    response = member.patch(f"/api/v1/question/{created['name']}", json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_no_fields_to_update"}


def test_topic_delete_detaches_question(member):
    topic = member.post(
        "/api/v1/topic", json={"title": "Temp", "category": "cub"}
    ).get_json()
    created = _create(member, topicId=topic["name"]).get_json()
    assert member.delete(f"/api/v1/topic/{topic['name']}").status_code == 204

    detail = member.get(f"/api/v1/question/{created['name']}").get_json()
    assert "topicId" not in detail
