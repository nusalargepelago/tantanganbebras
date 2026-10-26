import pytest

TOPIC_ITEM_KEYS = {"name", "title", "category", "idx", "creatorId", "createdAt", "updatedAt"}


def _create(client, **overrides):
    payload = {"title": "Pola dan Urutan", "category": "cub", "idx": 0}
    payload.update(overrides)
    return client.post("/api/v1/topic", json=payload)


def test_list_requires_login(client):
    response = client.get("/api/v1/topic")
    assert response.status_code == 401
    assert response.get_json() == {"message": "unauthorized"}


def test_list_is_paginated(member):
    body = member.get("/api/v1/topic").get_json()
    assert set(body) == {"items", "total", "page", "perPage"}
    assert body["total"] == 0
    assert body["page"] == 1
    assert body["perPage"] == 20


def test_list_rejects_bad_pagination(member):
    response = member.get("/api/v1/topic", query_string={"page": "abc"})
    assert response.status_code == 400
    assert response.get_json() == {"message": "page_must_be_integer"}


def test_create_topic(member):
    response = _create(member)
    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == TOPIC_ITEM_KEYS
    assert body["name"] == "pola-dan-urutan"
    assert body["title"] == "Pola dan Urutan"
    assert body["category"] == "cub"
    assert body["createdAt"].endswith("+00:00")


def test_create_topic_requires_title(member):
    response = member.post("/api/v1/topic", json={"category": "cub"})
    assert response.status_code == 400
    assert response.get_json() == {"message": "title_required"}


def test_create_topic_rejects_invalid_category(member):
    response = _create(member, category="elementary")
    assert response.status_code == 400
    assert response.get_json() == {"message": "category_invalid"}


def test_create_topic_whitespace_title_is_conflict(member):
    response = _create(member, title="   ")
    assert response.status_code == 409
    assert response.get_json() == {"message": "title_required"}


def test_create_duplicate_title_gets_suffix(member):
    first = _create(member).get_json()
    second = _create(member).get_json()
    assert first["name"] == "pola-dan-urutan"
    assert second["name"] == "pola-dan-urutan-0001"


def test_get_topic_404(member):
    response = member.get("/api/v1/topic/nope")
    assert response.status_code == 404
    assert response.get_json() == {"message": "topic_not_found"}


def test_get_topic_roundtrip(member):
    created = _create(member).get_json()
    fetched = member.get(f"/api/v1/topic/{created['name']}").get_json()
    assert fetched == created


def test_update_topic(member):
    created = _create(member).get_json()
    response = member.patch(
        f"/api/v1/topic/{created['name']}", json={"title": "Judul Baru", "idx": 5}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["title"] == "Judul Baru"
    assert body["idx"] == 5
    assert body["name"] == created["name"]


def test_update_topic_empty_body(member):
    created = _create(member).get_json()
    response = member.patch(f"/api/v1/topic/{created['name']}", json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_no_fields_to_update"}


def test_list_filters_by_category(member):
    _create(member, title="Scout Topic", category="scout")
    body = member.get("/api/v1/topic", query_string={"category": "scout"}).get_json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "scout"


def test_delete_topic(member):
    created = _create(member).get_json()
    response = member.delete(f"/api/v1/topic/{created['name']}")
    assert response.status_code == 204
    assert member.get(f"/api/v1/topic/{created['name']}").status_code == 404


def test_reorder_updates_idx_and_skips_unknown(member):
    a = _create(member, title="Topic A").get_json()
    b = _create(member, title="Topic B").get_json()
    response = member.post(
        "/api/v1/topic/reorder",
        json={"items": [{"name": a["name"], "idx": 10}, {"name": "ghost", "idx": 3}]},
    )
    assert response.status_code == 200
    assert response.get_json() == {"count": 1}
    assert member.get(f"/api/v1/topic/{a['name']}").get_json()["idx"] == 10
    assert member.get(f"/api/v1/topic/{b['name']}").get_json()["idx"] == 0


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"items": "nope"}, "items_must_be_list"),
        ({"items": [{"name": "a", "idx": "x"}]}, "items_idx_invalid"),
        ({"items": [{"idx": 1}]}, "items_name_required"),
        ({"items": ["a"]}, "items_malformed"),
    ],
)
def test_reorder_rejects_bad_items(member, body, message):
    response = member.post("/api/v1/topic/reorder", json=body)
    assert response.status_code == 400
    assert response.get_json() == {"message": message}
