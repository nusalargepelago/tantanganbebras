MENU_URL = "/api/v1/account/menu-preferences"


def test_menu_preferences_require_authentication(client):
    assert client.get(MENU_URL).status_code == 401
    assert (
        client.put(MENU_URL, json={"order": [], "hidden": []}).status_code == 401
    )


def test_menu_preferences_default_to_empty(member):
    response = member.get(MENU_URL)
    assert response.status_code == 200
    assert response.get_json() == {"order": [], "hidden": []}


def test_menu_preferences_round_trip(member):
    payload = {"order": ["Dashboard"], "hidden": ["Dashboard"]}

    response = member.put(MENU_URL, json=payload)
    assert response.status_code == 200
    assert response.get_json() == payload
    assert member.get(MENU_URL).get_json() == payload


def test_menu_preferences_update_in_place(member):
    member.put(MENU_URL, json={"order": ["Dashboard"], "hidden": []})
    response = member.put(
        MENU_URL, json={"order": ["Dashboard"], "hidden": ["Dashboard"]}
    )

    assert response.status_code == 200
    assert member.get(MENU_URL).get_json() == {
        "order": ["Dashboard"],
        "hidden": ["Dashboard"],
    }


def test_menu_preferences_are_scoped_to_the_owner(member, admin):
    member.put(MENU_URL, json={"order": ["Dashboard"], "hidden": ["Dashboard"]})

    assert admin.get(MENU_URL).get_json() == {"order": [], "hidden": []}


def test_menu_preferences_accept_unknown_keys(member):
    payload = {"order": ["Retired", "Dashboard"], "hidden": ["Removed"]}

    response = member.put(MENU_URL, json=payload)
    assert response.status_code == 200
    assert response.get_json() == payload


def test_menu_preferences_reject_duplicate_keys(member):
    response = member.put(
        MENU_URL, json={"order": ["Dashboard", "Dashboard"], "hidden": []}
    )

    assert response.status_code == 400
    assert response.get_json() == {"message": "order_duplicate_menu_key"}


def test_menu_preferences_reject_blank_keys(member):
    response = member.put(MENU_URL, json={"order": ["  "], "hidden": []})

    assert response.status_code == 400
    assert response.get_json() == {"message": "order_invalid_menu_key"}


def test_menu_preferences_reject_oversized_list(member):
    response = member.put(
        MENU_URL, json={"order": [f"menu-{i}" for i in range(101)], "hidden": []}
    )

    assert response.status_code == 400
    assert response.get_json() == {"message": "order_too_many_menu_items"}


def test_menu_preferences_ignore_unknown_fields(member):
    response = member.put(
        MENU_URL,
        json={"order": ["Dashboard"], "hidden": [], "unexpected": "ignored"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"order": ["Dashboard"], "hidden": []}


def test_menu_preferences_enforce_key_length(member):
    allowed = "a" * 64
    response = member.put(MENU_URL, json={"order": [allowed], "hidden": []})
    assert response.status_code == 200

    response = member.put(MENU_URL, json={"order": ["a" * 65], "hidden": []})
    assert response.status_code == 400
    assert response.get_json() == {"message": "order_invalid_menu_key"}


def test_menu_preferences_empty_payload_resets(member):
    member.put(MENU_URL, json={"order": ["Dashboard"], "hidden": ["Dashboard"]})

    response = member.put(MENU_URL, json={})

    assert response.status_code == 200
    assert response.get_json() == {"order": [], "hidden": []}
    assert member.get(MENU_URL).get_json() == {"order": [], "hidden": []}


def test_menu_preferences_tolerate_stored_payload_drift(app, member):
    from app.account.models import UserPreference
    from app.auth.models import User
    from framework.extensions import db

    with app.app_context():
        user_id = db.session.scalar(
            db.select(User.id).where(User.email == "member@example.com")
        )
        db.session.add(
            UserPreference(user_id=user_id, key="menu", value="{not-json")
        )
        db.session.commit()

    assert member.get(MENU_URL).get_json() == {"order": [], "hidden": []}

    with app.app_context():
        row = db.session.scalar(
            db.select(UserPreference).where(UserPreference.user_id == user_id)
        )
        row.value = '{"order": [1, "Dashboard"], "hidden": "legacy"}'
        db.session.commit()

    assert member.get(MENU_URL).get_json() == {"order": ["Dashboard"], "hidden": []}
