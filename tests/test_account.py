import pytest
from conftest import csrf_client, register

USER_ITEM_KEYS = {
    "id",
    "email",
    "username",
    "fullName",
    "appRole",
    "roles",
    "isActive",
    "createdOn",
}


def find_user(client, username):
    items = client.get("/api/v1/account/users").get_json()["items"]
    return next(item for item in items if item["username"] == username)


def test_list_users_requires_authentication(client):
    response = client.get("/api/v1/account/users")
    assert response.status_code == 401
    assert response.get_json() == {"message": "unauthorized"}


def test_list_users_requires_admin(member):
    response = member.get("/api/v1/account/users")
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_list_users_is_paginated(admin):
    body = admin.get("/api/v1/account/users").get_json()
    assert set(body) == {"items", "total", "page", "perPage"}
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["perPage"] == 20


def test_list_users_items_are_camel_case(admin):
    item = admin.get("/api/v1/account/users").get_json()["items"][0]
    assert set(item) == USER_ITEM_KEYS


def test_list_users_rejects_invalid_pagination(admin):
    response = admin.get("/api/v1/account/users", query_string={"page": "abc"})
    assert response.status_code == 400
    assert response.get_json() == {"message": "page_must_be_integer"}


def test_user_detail_matches_list_item(admin):
    detail = admin.get(f"/api/v1/account/users/{find_user(admin, 'admin')['id']}")
    assert detail.status_code == 200
    assert set(detail.get_json()) == USER_ITEM_KEYS


def test_update_user_is_camel_case(admin, member):
    member_id = find_user(admin, "member")["id"]

    response = admin.patch(
        f"/api/v1/account/users/{member_id}", json={"fullName": "Renamed Person"}
    )
    assert response.status_code == 200

    body = response.get_json()
    assert body["fullName"] == "Renamed Person"
    assert "full_name" not in body
    assert find_user(admin, "member")["fullName"] == "Renamed Person"


def test_update_user_requires_admin(member):
    response = member.patch(
        "/api/v1/account/users/some-id", json={"fullName": "Nope"}
    )
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_update_user_rejects_unknown_role(admin, member):
    member_id = find_user(admin, "member")["id"]

    response = admin.patch(
        f"/api/v1/account/users/{member_id}", json={"roleNames": ["Ghost"]}
    )
    assert response.status_code == 422
    assert response.get_json() == {"message": "role_not_found"}


def test_update_user_rejects_empty_body(admin, member):
    member_id = find_user(admin, "member")["id"]

    response = admin.patch(f"/api/v1/account/users/{member_id}", json={})
    assert response.status_code == 400
    assert set(response.get_json()) == {"message"}


def test_update_user_enforces_full_name_length(admin, member):
    member_id = find_user(admin, "member")["id"]

    response = admin.patch(
        f"/api/v1/account/users/{member_id}", json={"fullName": ""}
    )
    assert response.status_code == 400
    assert set(response.get_json()) == {"message"}
    assert find_user(admin, "member")["fullName"] == "Member User"


def test_update_user_rejects_invalid_app_role(admin, member):
    member_id = find_user(admin, "member")["id"]

    response = admin.patch(
        f"/api/v1/account/users/{member_id}", json={"app_role": "superuser"}
    )
    assert response.status_code == 400
    assert set(response.get_json()) == {"message"}


@pytest.mark.parametrize(
    "payload",
    [
        {"appRole": "admin"},
        {"isActive": False},
        {"roleNames": ["Member"]},
        {"fullName": "Renamed Camel"},
    ],
)
def test_update_user_accepts_camel_case_keys(admin, member, payload):
    """Wire format is camelCase — a round-trip of a presenter payload must work."""
    member_id = find_user(admin, "member")["id"]

    response = admin.patch(f"/api/v1/account/users/{member_id}", json=payload)
    assert response.status_code == 200, response.get_json()


def test_missing_user_is_404(admin):
    response = admin.get("/api/v1/account/users/no-such-user")
    assert response.status_code == 404
    assert response.get_json() == {"message": "user_not_found"}


def test_create_role_returns_201(admin):
    response = admin.post("/api/v1/account/roles", json={"name": "Reviewer"})
    assert response.status_code == 201
    assert response.get_json()["name"] == "Reviewer"


def test_create_role_requires_admin(member):
    response = member.post("/api/v1/account/roles", json={"name": "Reviewer"})
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_create_duplicate_role_is_409(admin):
    admin.post("/api/v1/account/roles", json={"name": "Reviewer"})

    response = admin.post("/api/v1/account/roles", json={"name": "Reviewer"})
    assert response.status_code == 409
    assert response.get_json() == {"message": "role_already_exists"}


def test_create_role_rejects_blank_name(admin):
    response = admin.post("/api/v1/account/roles", json={"name": ""})
    assert response.status_code == 400
    assert set(response.get_json()) == {"message"}


def test_update_role(admin):
    role_id = admin.post("/api/v1/account/roles", json={"name": "Temp"}).get_json()[
        "id"
    ]

    response = admin.patch(f"/api/v1/account/roles/{role_id}", json={"name": "Temp2"})
    assert response.status_code == 200
    assert response.get_json()["name"] == "Temp2"


def test_delete_builtin_role_is_rejected(admin):
    roles = admin.get("/api/v1/account/roles").get_json()["items"]
    member_role = next(role for role in roles if role["name"] == "Member")

    response = admin.delete(f"/api/v1/account/roles/{member_role['id']}")
    assert response.status_code == 422
    assert response.get_json() == {"message": "cannot_delete_builtin_role"}


def test_delete_role_is_204(admin):
    role_id = admin.post("/api/v1/account/roles", json={"name": "Temp"}).get_json()[
        "id"
    ]

    response = admin.delete(f"/api/v1/account/roles/{role_id}")
    assert response.status_code == 204
    assert response.get_data() == b""


def test_delete_missing_role_is_404(admin):
    response = admin.delete("/api/v1/account/roles/no-such-role")
    assert response.status_code == 404
    assert response.get_json() == {"message": "role_not_found"}


def test_promoted_user_gains_admin_access(admin, app):
    newcomer = csrf_client(app)
    response = register(newcomer, email="new@example.com", username="newbie")
    assert response.status_code == 201
    newcomer_id = response.get_json()["id"]
    assert newcomer.get("/api/v1/account/users").status_code == 403

    promoted = admin.patch(
        f"/api/v1/account/users/{newcomer_id}", json={"app_role": "admin"}
    )
    assert promoted.status_code == 200
    assert promoted.get_json()["appRole"] == "admin"
    assert newcomer.get("/api/v1/account/users").status_code == 200


def test_create_user(admin):
    response = admin.post(
        "/api/v1/account/users",
        json={
            "email": "creator@example.com",
            "password": "S3cret!pass",
            "fullName": "Course Creator",
            "appRole": "user",
        },
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["email"] == "creator@example.com"
    assert body["username"] == "creator@example.com"
    assert body["appRole"] == "user"


def test_create_user_duplicate_email(admin):
    admin.post(
        "/api/v1/account/users",
        json={"email": "dup@example.com", "password": "S3cret!pass", "fullName": "Dup"},
    )
    response = admin.post(
        "/api/v1/account/users",
        json={"email": "dup@example.com", "password": "S3cret!pass", "fullName": "Dup"},
    )
    assert response.status_code == 409
    assert response.get_json() == {"message": "email_already_registered"}


def test_create_user_requires_admin(member):
    response = member.post(
        "/api/v1/account/users",
        json={"email": "x@example.com", "password": "S3cret!pass", "fullName": "X"},
    )
    assert response.status_code == 403


def test_delete_user(admin):
    created = admin.post(
        "/api/v1/account/users",
        json={"email": "gone@example.com", "password": "S3cret!pass", "fullName": "Gone"},
    ).get_json()
    response = admin.delete(f"/api/v1/account/users/{created['id']}")
    assert response.status_code == 204
    assert admin.get(f"/api/v1/account/users/{created['id']}").status_code == 404
