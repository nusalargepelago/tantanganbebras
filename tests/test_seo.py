from __future__ import annotations

import pytest

from app.infra.seo import (
    get_app_lang,
    get_brand,
    index_context,
    save_app_lang,
    save_brand,
)
from framework.extensions import db
from framework.infra.frontend import _render_index_html

MINIMAL_INDEX = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Tantangan Bebras</title>
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


def _write_index(tmp_path):
    (tmp_path / "index.html").write_text(MINIMAL_INDEX, encoding="utf-8")
    return str(tmp_path)


def test_get_brand_returns_defaults_when_empty(app):
    with app.app_context():
        assert get_brand() == {
            "name": "Tantangan Bebras",
            "tagline": "",
            "description": "",
            "siteUrl": "",
        }


def test_get_brand_falls_back_when_settings_table_missing(app):
    from app.infra.models import AppSetting

    with app.app_context():
        AppSetting.__table__.drop(db.engine)

        assert get_brand()["name"] == "Tantangan Bebras"


def test_save_brand_upserts_rows(app):
    from app.infra.models import AppSetting

    with app.app_context():
        save_brand(db.session, {"name": "Acme", "siteUrl": ""})
        db.session.commit()

        rows = db.session.scalars(db.select(AppSetting)).all()
        assert len(rows) == len(("name", "tagline", "description", "siteUrl"))
        name_row = db.session.scalar(
            db.select(AppSetting).where(AppSetting.key == "name")
        )
        assert name_row.value == "Acme"

        save_brand(db.session, {"name": "Acme 2"})
        db.session.commit()
        rows = db.session.scalars(db.select(AppSetting)).all()
        assert len(rows) == 4
        assert name_row.value == "Acme 2"


def test_index_context_builds_seo_from_brand(app):
    with app.app_context():
        save_brand(
            db.session,
            {
                "name": "Acme Corp",
                "tagline": "Work less",
                "description": "",
                "siteUrl": "https://acme.test/",
            },
        )
        db.session.commit()

        ctx = index_context()

    assert ctx["brand"]["name"] == "Acme Corp"
    seo = ctx["seo"]
    assert seo["title"] == "Acme Corp"
    assert seo["description"] == "Work less"
    assert seo["canonical"] == "https://acme.test"
    assert seo["robots"] == "index, follow"
    assert seo["lang"] == "en"


def test_index_context_noindex_when_disabled(app):
    app.config["SEO_INDEXABLE"] = False

    with app.app_context():
        assert index_context()["seo"]["robots"] == "noindex, nofollow"


def test_get_app_lang_defaults_to_en(app):
    with app.app_context():
        assert get_app_lang() == "en"


def test_get_app_lang_falls_back_to_config(app):
    app.config["APP_LANG"] = "id"

    with app.app_context():
        assert get_app_lang() == "id"


def test_get_app_lang_ignores_unsupported_config(app):
    app.config["APP_LANG"] = "fr"

    with app.app_context():
        assert get_app_lang() == "en"


def test_get_app_lang_falls_back_when_settings_table_missing(app):
    from app.infra.models import AppSetting

    with app.app_context():
        AppSetting.__table__.drop(db.engine)

        assert get_app_lang() == "en"


def test_save_app_lang_upserts_single_row(app):
    from app.infra.models import AppSetting

    with app.app_context():
        save_app_lang(db.session, "id")
        db.session.commit()

        rows = db.session.scalars(
            db.select(AppSetting).where(AppSetting.key == "appLang")
        ).all()
        assert len(rows) == 1
        assert rows[0].value == "id"

        save_app_lang(db.session, "en")
        db.session.commit()

        rows = db.session.scalars(
            db.select(AppSetting).where(AppSetting.key == "appLang")
        ).all()
        assert len(rows) == 1
        assert rows[0].value == "en"


def test_index_context_exposes_app_lang(app):
    with app.app_context():
        assert index_context()["appLang"] == "en"
        assert index_context()["seo"]["lang"] == "en"


def test_request_lang_prefers_cookie_over_app_default(app):
    with app.app_context():
        with app.test_request_context("/", headers={"Cookie": "minimals-lang=id"}):
            ctx = index_context()

    assert ctx["seo"]["lang"] == "id"
    assert ctx["appLang"] == "en"


def test_index_context_seo_lang_follows_saved_app_lang(app):
    with app.app_context():
        save_app_lang(db.session, "id")
        db.session.commit()

        with app.test_request_context("/"):
            ctx = index_context()

    assert ctx["seo"]["lang"] == "id"
    assert ctx["appLang"] == "id"


def test_index_lang_follows_language_cookie(app):
    with app.test_request_context("/", headers={"Cookie": "minimals-lang=id"}):
        assert index_context()["seo"]["lang"] == "id"

    with app.test_request_context("/", headers={"Cookie": "minimals-lang=xx"}):
        assert index_context()["seo"]["lang"] == "en"

    with app.app_context():
        assert index_context()["seo"]["lang"] == "en"


def test_render_injects_seo_tags_and_boot(app, tmp_path):
    root = _write_index(tmp_path)

    def provider():
        return {
            "brand": {"name": "Acme"},
            "seo": {
                "title": "Acme",
                "lang": "id",
                "description": "Acme helps you work less.",
                "robots": "index, follow",
                "canonical": "https://acme.test",
            },
        }

    with app.test_request_context("/"):
        html = _render_index_html(root, provider)

    assert '<html lang="id">' in html
    assert "<title>Acme</title>" in html
    assert '<meta name="description" content="Acme helps you work less." />' in html
    assert '<link rel="canonical" href="https://acme.test" />' in html
    assert '<meta property="og:title" content="Acme" />' in html
    assert '<meta property="og:url" content="https://acme.test" />' in html
    assert '<meta name="robots" content="index, follow" />' in html
    assert "window[\"brand\"]" in html
    assert "window[\"seo\"]" not in html
    assert "csrfToken" in html


def test_render_survives_provider_failure(app, tmp_path):
    root = _write_index(tmp_path)

    def boom():
        raise RuntimeError("storage down")

    with app.test_request_context("/"):
        html = _render_index_html(root, boom)

    assert "csrfToken" in html
    assert "<title>Tantangan Bebras</title>" in html


def test_render_escapes_seo_values(app, tmp_path):
    root = _write_index(tmp_path)

    def provider():
        return {"seo": {"title": "<script>alert(1)</script>"}}

    with app.test_request_context("/"):
        html = _render_index_html(root, provider)

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


@pytest.mark.parametrize("provider_result", [None, {}])
def test_render_without_seo_keeps_static_head(app, tmp_path, provider_result):
    root = _write_index(tmp_path)

    with app.test_request_context("/"):
        html = _render_index_html(root, lambda: provider_result)

    assert "<title>Tantangan Bebras</title>" in html
    assert 'name="description"' not in html


def test_robots_txt_allows_crawling(client):
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")
    body = response.get_data(as_text=True)
    assert body.startswith("User-Agent: *")
    assert "Allow: /" in body
    assert "Disallow: /api/" in body
    assert "Sitemap:" not in body


def test_robots_txt_disallows_everything_when_noindex(client, app):
    app.config["SEO_INDEXABLE"] = False

    body = client.get("/robots.txt").get_data(as_text=True)

    assert body == "User-Agent: *\nDisallow: /\n"
    assert "Sitemap:" not in body


def test_robots_txt_uses_brand_site_url(app, client):
    with app.app_context():
        save_brand(db.session, {"name": "Acme", "siteUrl": "https://acme.test"})
        db.session.commit()

    body = client.get("/robots.txt").get_data(as_text=True)

    assert "Sitemap: https://acme.test/sitemap.xml" in body


def test_sitemap_xml_empty_without_site_url(client):
    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert response.content_type.startswith("application/xml")
    body = response.get_data(as_text=True)
    assert "<?xml version" in body
    assert "<loc>" not in body


def test_sitemap_xml_prefers_brand_site_url(app, client):
    with app.app_context():
        save_brand(db.session, {"name": "Acme", "siteUrl": "https://acme.test"})
        db.session.commit()

    body = client.get("/sitemap.xml").get_data(as_text=True)

    assert "<loc>https://acme.test/</loc>" in body


def test_host_header_does_not_leak_into_seo(app, client):
    with app.app_context():
        save_brand(db.session, {"name": "Acme", "siteUrl": ""})
        db.session.commit()

        with app.test_request_context("/", headers={"Host": "evil.example"}):
            assert index_context()["seo"]["canonical"] == ""

    robots = client.get("/robots.txt", headers={"Host": "evil.example"})
    assert "Sitemap:" not in robots.get_data(as_text=True)

    sitemap = client.get("/sitemap.xml", headers={"Host": "evil.example"})
    assert "<loc>" not in sitemap.get_data(as_text=True)


def test_crawler_endpoints_are_exempt_from_rate_limits():
    from framework.extensions.rate_limit import limiter

    assert "seo" in limiter.limit_manager._blueprint_exemptions
