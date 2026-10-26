from conftest import register


def test_register_returns_flat_camel_case_user(client):
    response = register(client)
    assert response.status_code == 201

    body = response.get_json()
    assert body["email"] == "alice@example.com"
    assert body["username"] == "alice"
    assert body["fullName"] == "Alice Doe"
    assert body["appRole"] == "user"
    assert body["isActive"] is True
    assert body["createdOn"]
    assert not {"full_name", "app_role", "is_active", "created_on"} & body.keys()


def test_register_signs_the_user_in(client):
    register(client)
    assert client.get("/api/v1/auth/me").status_code == 200


def test_register_rejects_duplicate_email(client):
    register(client)
    client.get("/api/v1/auth/logout")

    response = register(client, username="someone_else")
    assert response.status_code == 409
    assert response.get_json() == {"message": "email_already_registered"}


def test_register_rejects_duplicate_username(client):
    register(client)
    client.get("/api/v1/auth/logout")

    response = register(client, email="other@example.com")
    assert response.status_code == 409
    assert response.get_json() == {"message": "username_taken"}


def test_register_rejects_email_differing_only_by_case(client):
    register(client)
    client.get("/api/v1/auth/logout")

    response = register(client, email="ALICE@example.com", username="someone_else")
    assert response.status_code == 409
    assert response.get_json() == {"message": "email_already_registered"}


def test_register_rejects_username_differing_only_by_case(client):
    register(client)
    client.get("/api/v1/auth/logout")

    response = register(client, email="other@example.com", username="ALICE")
    assert response.status_code == 409
    assert response.get_json() == {"message": "username_taken"}


def test_register_rejects_invalid_email(client):
    response = register(client, email="not-an-email")
    assert response.status_code == 400
    assert response.get_json() == {"message": "email_invalid_email"}


def test_register_rejects_short_password(client):
    response = register(client, password="Ab1!def")
    assert response.status_code == 400
    assert response.get_json() == {
        "message": "password_must_be_at_least_8_characters"
    }


def test_register_rejects_overlong_email(client):
    response = register(client, email="a" * 250 + "@example.com")
    assert response.status_code == 400
    assert response.get_json() == {"message": "email_too_long"}


def test_register_rejects_overlong_full_name(client):
    response = register(client, fullName="N" * 256)
    assert response.status_code == 400
    body = response.get_json()
    assert set(body) == {"message"}
    assert body["message"].endswith("_too_long")


def test_register_rejects_password_without_digit(client):
    response = register(client, password="Strng!Pass")
    assert response.status_code == 400
    assert response.get_json() == {
        "message": "password_password_must_contain_digit"
    }


def test_register_requires_full_name(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "a@example.com", "username": "abcd", "password": "Str0ng!Pass"},
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "full_name_required"}


def test_register_rejects_blank_username(client):
    response = register(client, username="   ")

    assert response.status_code == 400
    assert response.get_json() == {
        "message": "username_must_be_at_least_3_characters"
    }


def test_register_rejects_username_shorter_than_minimum_after_trim(client):
    response = register(client, username="  ab  ")

    assert response.status_code == 400
    assert response.get_json() == {
        "message": "username_must_be_at_least_3_characters"
    }


def test_register_trims_username_before_length_check(client):
    response = register(client, username="  bob  ")

    assert response.status_code == 201
    assert response.get_json()["username"] == "bob"


def test_register_rejects_email_without_local_part(client):
    response = register(client, email="@example.com")

    assert response.status_code == 400
    assert response.get_json() == {"message": "email_invalid_email"}


def test_register_rejects_email_without_domain_suffix(client):
    response = register(client, email="alice@localhost")

    assert response.status_code == 400
    assert response.get_json() == {"message": "email_invalid_email"}


def test_register_accepts_subdomain_and_tagged_email(client):
    response = register(client, email="alice+billing@mail.example.co.id")

    assert response.status_code == 201


def test_login_rejects_blank_identifier(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "   ", "password": "Str0ng!Pass"},
    )

    assert response.status_code == 400


def test_login_returns_the_user(client):
    register(client)
    client.get("/api/v1/auth/logout")

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "alice", "password": "Str0ng!Pass"},
    )
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"


def test_login_accepts_email_as_identifier(client):
    register(client)
    client.get("/api/v1/auth/logout")

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "ALICE@example.com", "password": "Str0ng!Pass"},
    )
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"


def test_login_matches_stored_identifier_regardless_of_casing(client):
    register(client, email="Mixed@Example.com", username="MixedUser")
    client.get("/api/v1/auth/logout")

    by_username = client.post(
        "/api/v1/auth/login",
        json={"identifier": "MIXEDUSER", "password": "Str0ng!Pass"},
    )
    assert by_username.status_code == 200
    assert by_username.get_json()["username"] == "mixeduser"

    client.get("/api/v1/auth/logout")
    by_email = client.post(
        "/api/v1/auth/login",
        json={"identifier": "mixed@EXAMPLE.com", "password": "Str0ng!Pass"},
    )
    assert by_email.status_code == 200
    assert by_email.get_json()["email"] == "mixed@example.com"


def test_login_finds_stored_mixed_case_row(client, app):
    from framework.extensions import db

    register(client, email="stored@mixed.com", username="storedmixed")
    client.get("/api/v1/auth/logout")

    with app.app_context():
        from app.auth.models import User

        user = db.session.scalar(
            db.select(User).where(User.username == "storedmixed")
        )
        assert user is not None
        user.username = "StoredMixed"
        user.email = "Stored@Mixed.com"
        db.session.commit()

    by_username = client.post(
        "/api/v1/auth/login",
        json={"identifier": "storedmixed", "password": "Str0ng!Pass"},
    )
    assert by_username.status_code == 200
    assert by_username.get_json()["username"] == "StoredMixed"

    client.get("/api/v1/auth/logout")
    by_email = client.post(
        "/api/v1/auth/login",
        json={"identifier": "stored@mixed.com", "password": "Str0ng!Pass"},
    )
    assert by_email.status_code == 200


def test_login_rejects_wrong_password(client):
    register(client)
    client.get("/api/v1/auth/logout")

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "alice", "password": "Wr0ng!Pass"},
    )
    assert response.status_code == 401
    assert response.get_json() == {"message": "invalid_credentials"}


def test_login_rejects_unknown_identifier(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "ghost", "password": "Str0ng!Pass"},
    )
    assert response.status_code == 401
    assert response.get_json() == {"message": "invalid_credentials"}


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.get_json() == {"message": "unauthorized"}


def test_logout_ends_the_session(client):
    register(client)

    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_registration_mode_defaults_to_open(client):
    response = client.get("/api/v1/auth/registration")

    assert response.status_code == 200
    assert response.get_json() == {"mode": "open"}


def test_registration_gate_fails_open_without_settings_table(client, app):
    from app.infra.models import AppSetting
    from framework.extensions import db

    with app.app_context():
        AppSetting.__table__.drop(db.engine)

    assert client.get("/api/v1/auth/registration").get_json() == {"mode": "open"}
    assert register(client).status_code == 201


def test_admin_closes_registration_and_register_is_blocked(admin, client):
    response = admin.put("/api/v1/auth/registration", json={"mode": "closed"})
    assert response.status_code == 200
    assert response.get_json() == {"mode": "closed"}

    assert client.get("/api/v1/auth/registration").get_json() == {"mode": "closed"}

    blocked = register(client)
    assert blocked.status_code == 403
    assert blocked.get_json() == {"message": "registration_disabled"}


def test_admin_reopens_registration(admin, client):
    admin.put("/api/v1/auth/registration", json={"mode": "closed"})

    response = admin.put("/api/v1/auth/registration", json={"mode": "open"})
    assert response.status_code == 200
    assert response.get_json() == {"mode": "open"}

    assert register(client).status_code == 201


def test_registration_mode_change_is_audited(admin, app):
    from app.infra.audit import AuditLog
    from framework.extensions import db

    admin.put("/api/v1/auth/registration", json={"mode": "closed"})

    with app.app_context():
        row = db.session.scalar(
            db.select(AuditLog).where(
                AuditLog.action == "registration_mode_changed"
            )
        )
    assert row is not None
    assert row.user_id is not None
    assert row.details == {"mode": "closed"}


def test_set_registration_mode_requires_admin(member):
    response = member.put("/api/v1/auth/registration", json={"mode": "closed"})

    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_set_registration_mode_requires_login(client):
    response = client.put("/api/v1/auth/registration", json={"mode": "closed"})

    assert response.status_code == 401
    assert response.get_json() == {"message": "unauthorized"}


def test_set_registration_mode_rejects_invalid_mode(admin):
    response = admin.put("/api/v1/auth/registration", json={"mode": "maybe"})

    assert response.status_code == 400
    assert response.get_json() == {"message": "mode_invalid"}


def test_set_registration_mode_requires_mode(admin):
    response = admin.put("/api/v1/auth/registration", json={})

    assert response.status_code == 400
    assert response.get_json() == {"message": "mode_required"}


def test_login_works_while_registration_closed(admin, client):
    admin.put("/api/v1/auth/registration", json={"mode": "closed"})

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@example.com", "password": "Str0ng!Pass"},
    )
    assert response.status_code == 200
    assert response.get_json()["username"] == "admin"
