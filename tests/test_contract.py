import re

import pytest

SNAKE_KEY = re.compile(r"[a-z0-9]+_[a-z0-9]+")
ERROR_KEY = re.compile(r"^[a-z0-9_]+$")


def assert_error(response, status):
    body = response.get_json()
    assert response.status_code == status
    assert isinstance(body, dict)
    assert set(body) == {"message"}
    assert ERROR_KEY.match(body["message"]), body["message"]


def all_keys(node, found=None):
    found = set() if found is None else found
    if isinstance(node, dict):
        for key, value in node.items():
            found.add(key)
            all_keys(value, found)
    elif isinstance(node, list):
        for value in node:
            all_keys(value, found)
    return found


def test_unknown_route_uses_error_shape(client):
    assert_error(client.get("/api/v1/does-not-exist"), 404)


def test_delete_returns_204_with_no_body(admin):
    role_id = admin.post(
        "/api/v1/account/roles", json={"name": "Temporary"}
    ).get_json()["id"]

    response = admin.delete(f"/api/v1/account/roles/{role_id}")

    assert response.status_code == 204
    assert response.get_data() == b""


def test_unmapped_pydantic_errors_keep_the_snake_case_contract():
    from framework.base import DTOBase
    from framework.exceptions import ValidationFailed

    class Probe(DTOBase):
        tags: list[str] = DTOBase.field(default_factory=list, min_length=3)

    with pytest.raises(ValidationFailed) as excinfo:
        Probe.validate({"tags": []})

    key = excinfo.value.message
    assert ERROR_KEY.match(key), key


def test_validation_failure_uses_error_shape(client):
    assert_error(client.post("/api/v1/auth/login", json={}), 400)


def test_authentication_failure_uses_error_shape(client):
    assert_error(client.get("/api/v1/auth/me"), 401)


def test_authorization_failure_uses_error_shape(member):
    assert_error(member.get("/api/v1/account/users"), 403)


def test_business_rule_failure_uses_error_shape(admin):
    admin.post("/api/v1/account/roles", json={"name": "Ops"})
    assert_error(
        admin.post("/api/v1/account/roles", json={"name": "Ops"}), 409
    )


def test_setup_db_error_uses_snake_case_key(client, tmp_path):
    """A driver failure must not leak a sentence into the error message."""
    client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite", "path": str(tmp_path / "ok.db")},
    )
    response = client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite", "path": str(tmp_path / "missing" / "x" / "\0bad")},
    )
    assert response.status_code == 400
    body = response.get_json()
    assert set(body) == {"message"}
    assert ERROR_KEY.match(body["message"]), body["message"]


def test_success_has_no_data_envelope(member):
    body = member.get("/api/v1/auth/me").get_json()
    assert "data" not in body
    assert "id" in body


def test_user_payload_has_no_snake_case_keys(member):
    body = member.get("/api/v1/auth/me").get_json()
    assert not [key for key in body if SNAKE_KEY.search(key)]


def test_health_payload_has_no_snake_case_keys(client):
    body = client.get("/health").get_json()
    assert not [key for key in all_keys(body) if SNAKE_KEY.search(key)]


def test_setup_status_is_camel_case(client):
    body = client.get("/api/v1/setup/status").get_json()
    assert set(body) == {"setupRequired", "reason", "activeEngine", "activeUrl"}


def test_setup_status_public_omits_db_details(client):
    response = client.get(
        "/api/v1/setup/status",
        environ_overrides={"REMOTE_ADDR": "203.0.113.7"},
    )
    assert response.status_code == 200
    assert set(response.get_json()) == {"setupRequired", "reason"}


def test_cross_service_ping(client):
    assert client.get("/api/v1/app/ping").get_json() == {
        "status": "ok",
        "service": "app",
    }


def test_cross_service_users_requires_authentication(client):
    assert_error(client.get("/api/v1/app/users"), 401)


def test_cross_service_users_requires_admin(member):
    assert_error(member.get("/api/v1/app/users"), 403)


def test_cross_service_users_accepts_internal_token(app):
    response = app.test_client().get(
        "/api/v1/app/users",
        headers={"X-Internal-Token": "internal-test-token"},
    )
    assert response.status_code == 200
    assert set(response.get_json()) == {"items"}


def test_list_endpoints_expose_items(admin):
    body = admin.get("/api/v1/account/roles").get_json()
    assert set(body) == {"items"}
    assert isinstance(body["items"], list)
