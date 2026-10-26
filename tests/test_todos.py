from conftest import csrf_client, register


def _create(client, **overrides):
    payload = {"title": "Buy milk", **overrides}
    return client.post("/api/v1/todos", json=payload)


def test_create_todo(member):
    response = _create(member, description="2%", completed=False, dueDate="2026-10-25")
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == "Buy milk"
    assert body["completed"] is False
    assert body["dueDate"] == "2026-10-25"
    assert body["creatorId"]


def test_create_requires_login(client):
    response = client.post("/api/v1/todos", json={"title": "x"})
    assert response.status_code == 401


def test_list_is_paginated_and_scoped(member):
    _create(member)
    body = member.get("/api/v1/todos").get_json()
    assert set(body) == {"items", "total", "page", "perPage"}
    assert body["total"] == 1


def test_list_admin_sees_all_users(admin, app):
    _create(admin)
    other = csrf_client(app)
    register(other, email="other@example.com", username="other", fullName="Other User")
    _create(other)

    assert admin.get("/api/v1/todos").get_json()["total"] == 2
    assert other.get("/api/v1/todos").get_json()["total"] == 1


def test_completed_filter(member):
    _create(member, completed=True)
    _create(member, completed=False)
    assert member.get("/api/v1/todos", query_string={"completed": "true"}).get_json()["total"] == 1
    assert member.get("/api/v1/todos", query_string={"completed": "false"}).get_json()["total"] == 1


def test_get_todo_owner_and_403(member, app):
    created = _create(member).get_json()
    assert member.get(f"/api/v1/todos/{created['id']}").status_code == 200

    other = csrf_client(app)
    register(other, email="other@example.com", username="other", fullName="Other User")
    assert other.get(f"/api/v1/todos/{created['id']}").status_code == 403


def test_get_missing_404(member):
    response = member.get("/api/v1/todos/nope")
    assert response.status_code == 404
    assert response.get_json() == {"message": "todo_not_found"}


def test_update_todo(member):
    created = _create(member).get_json()
    response = member.patch(
        f"/api/v1/todos/{created['id']}",
        json={"title": "Buy eggs", "completed": True, "dueDate": ""},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["title"] == "Buy eggs"
    assert body["completed"] is True
    assert body.get("dueDate") is None


def test_update_empty_body(member):
    created = _create(member).get_json()
    response = member.patch(f"/api/v1/todos/{created['id']}", json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_no_fields_to_update"}


def test_update_rejects_null_title(member):
    created = _create(member).get_json()
    response = member.patch(f"/api/v1/todos/{created['id']}", json={"title": None})
    assert response.status_code == 400
    assert response.get_json() == {"message": "title_required"}


def test_update_bad_due_date(member):
    created = _create(member).get_json()
    response = member.patch(f"/api/v1/todos/{created['id']}", json={"dueDate": "not-a-date"})
    assert response.status_code == 400
    assert response.get_json() == {"message": "due_date_invalid_date"}


def test_update_other_forbidden(member, app):
    created = _create(member).get_json()
    other = csrf_client(app)
    register(other, email="other@example.com", username="other", fullName="Other User")
    response = other.patch(f"/api/v1/todos/{created['id']}", json={"title": "hijack"})
    assert response.status_code == 403


def test_admin_can_update_and_delete_any(member, admin):
    created = _create(member).get_json()
    assert admin.patch(
        f"/api/v1/todos/{created['id']}", json={"title": "edited by admin"}
    ).status_code == 200
    assert admin.delete(f"/api/v1/todos/{created['id']}").status_code == 204
    assert member.get(f"/api/v1/todos/{created['id']}").status_code == 404


def test_delete_owner(member):
    created = _create(member).get_json()
    assert member.delete(f"/api/v1/todos/{created['id']}").status_code == 204
    assert member.get("/api/v1/todos").get_json()["total"] == 0
