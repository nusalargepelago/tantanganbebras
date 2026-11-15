from __future__ import annotations

import framework.infra.frontend as spa

MINIMAL_INDEX = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Minimals</title>
  </head>
  <body>
    <div id="app"></div>
    <script>
      {% for key in boot %}
      window["{{ key }}"] = {{ boot[key] | tojson }};
      {% endfor %}
    </script>
  </body>
</html>
"""


def test_root_reports_missing_build_when_spa_is_absent(app, monkeypatch):
    monkeypatch.setattr(spa, "has_frontend", lambda root: False)

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert response.get_json()["message"] == "spa_not_built"


def test_unknown_api_path_is_never_served_the_spa(app, monkeypatch):
    monkeypatch.setattr(spa, "has_frontend", lambda root: True)

    response = app.test_client().get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.get_json() == {"message": "not_found"}


def test_spa_assets_do_not_escape_the_static_root(app):
    response = app.test_client().get("/static/frontend/../../../app/config.py")

    assert response.status_code != 200
    assert b"SECRET_KEY" not in response.get_data()


def test_missing_upload_returns_404(client):
    response = client.get("/uploads/missing.png")

    assert response.status_code == 404


def test_index_response_is_no_cache(app, tmp_path):
    (tmp_path / "index.html").write_text(MINIMAL_INDEX, encoding="utf-8")

    with app.test_request_context("/"):
        html, status, headers = spa._serve_index(str(tmp_path), None)

    assert status == 200
    assert "Minimals" in html
    assert headers["Cache-Control"] == "no-cache"
