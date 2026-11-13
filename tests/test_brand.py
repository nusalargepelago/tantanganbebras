from __future__ import annotations

from uuid import uuid4

import pytest

from app.infra.seo import get_brand

BRAND_URL = "/api/v1/brand/logo"


def _url(name: str | None = None) -> str:
    return f"/uploads/{name or f'{uuid4()}.png'}"


def test_brand_logo_requires_authentication(client):
    response = client.put(BRAND_URL, json={"logoUrl": ""})

    assert response.status_code == 401


def test_member_cannot_update_logo(member):
    response = member.put(BRAND_URL, json={"logoUrl": _url()})

    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_admin_sets_and_clears_logo(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    url = _url()
    (tmp_path / url.removeprefix("/uploads/")).write_bytes(b"image")

    response = admin.put(BRAND_URL, json={"logoUrl": url})
    assert response.status_code == 200
    assert response.get_json() == {"logoUrl": url}
    with app.app_context():
        assert get_brand()["logoUrl"] == url

    response = admin.put(BRAND_URL, json={"logoUrl": ""})
    assert response.status_code == 200
    assert response.get_json() == {"logoUrl": ""}
    with app.app_context():
        assert get_brand()["logoUrl"] == ""


def test_admin_logo_trims_whitespace(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    url = _url()
    (tmp_path / url.removeprefix("/uploads/")).write_bytes(b"image")

    response = admin.put(BRAND_URL, json={"logoUrl": f"  {url}  "})

    assert response.status_code == 200
    assert response.get_json() == {"logoUrl": url}


def test_logo_rejects_missing_upload(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = admin.put(BRAND_URL, json={"logoUrl": _url()})

    assert response.status_code == 400
    assert response.get_json() == {"message": "logo_upload_missing"}
    with app.app_context():
        assert get_brand()["logoUrl"] == ""


def test_replacing_logo_deletes_previous_upload(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    old, new = _url(), _url()
    for url in (old, new):
        (tmp_path / url.removeprefix("/uploads/")).write_bytes(b"image")

    admin.put(BRAND_URL, json={"logoUrl": old})
    response = admin.put(BRAND_URL, json={"logoUrl": new})

    assert response.status_code == 200
    assert not (tmp_path / old.removeprefix("/uploads/")).exists()
    assert (tmp_path / new.removeprefix("/uploads/")).exists()


def test_clearing_logo_deletes_upload(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    url = _url()
    (tmp_path / url.removeprefix("/uploads/")).write_bytes(b"image")

    admin.put(BRAND_URL, json={"logoUrl": url})
    response = admin.put(BRAND_URL, json={"logoUrl": ""})

    assert response.status_code == 200
    assert not (tmp_path / url.removeprefix("/uploads/")).exists()


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.test/logo.png",
        "//evil.test/logo.png",
        "/uploads/../secret.png",
        "/uploads/logo.png",
        f"/uploads/{uuid4()}.svg",
        f"static/{uuid4()}.png",
    ],
)
def test_logo_rejects_non_upload_urls(admin, url):
    response = admin.put(BRAND_URL, json={"logoUrl": url})

    assert response.status_code == 400
    assert response.get_json() == {"message": "logo_url_invalid"}


def test_logo_requires_field(admin):
    response = admin.put(BRAND_URL, json={})

    assert response.status_code == 400
    assert response.get_json() == {"message": "logo_url_required"}
