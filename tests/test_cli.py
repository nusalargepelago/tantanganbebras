"""Terminal setup wizard (`app/cli.py`).

The CLI is the only way to run setup on a cPanel/Passenger host, so these
tests drive it the way an operator would: through prompts.
"""
from __future__ import annotations

import click
import pytest
from click.testing import CliRunner


@pytest.fixture()
def fresh_app(tmp_path, monkeypatch):
    """An app bound to a database file that does not exist yet.

    The shared ``app`` fixture pre-creates every table with ``create_all()``,
    which would collide with the wizard's own Alembic upgrade. Starting from an
    empty file exercises the migration the CLI actually runs.
    """
    from app import config as app_config
    from app.create_app import create_app
    from framework.extensions import db

    uri = "sqlite:///" + (tmp_path / "boot.db").as_posix()
    monkeypatch.setattr(app_config.Config, "SQLALCHEMY_DATABASE_URI", uri)

    application = create_app()
    application.config["TESTING"] = True
    yield application

    with application.app_context():
        db.session.remove()
        db.engine.dispose()


def _run(app, answers: list[str]):
    from app.cli import setup

    with app.app_context():
        return CliRunner().invoke(setup, input="\n".join(answers) + "\n")


def _answers(target, *, password: str = "Str0ng!Pass", lang: str = "id") -> list[str]:
    return [
        "sqlite",
        str(target),
        "boss@example.com",
        "",
        "Boss User",
        password,
        password,
        "Acme",
        "A tagline",
        "A description",
        "https://acme.test",
        lang,
    ]


def test_setup_command_creates_admin_and_brand(fresh_app, tmp_path):
    from app.auth.models import User
    from app.infra.models import AppSetting
    from framework.extensions import db

    result = _run(fresh_app, _answers(tmp_path / "setup.db"))

    assert result.exit_code == 0, result.output
    assert "Administrator created: boss@example.com" in result.output

    with fresh_app.app_context():
        user = db.session.query(User).filter_by(email="boss@example.com").one()
        assert user.username == "boss"
        assert user.app_role == "admin"
        assert [role.name for role in user.roles] == ["Member"]

        settings = {row.key: row.value for row in db.session.query(AppSetting)}
        assert settings["name"] == "Acme"
        assert settings["tagline"] == "A tagline"
        assert settings["siteUrl"] == "https://acme.test"
        assert settings["appLang"] == "id"


def test_setup_command_is_idempotent(fresh_app, tmp_path):
    first = _run(fresh_app, _answers(tmp_path / "setup.db"))
    assert first.exit_code == 0, first.output

    second = _run(fresh_app, [])

    assert second.exit_code == 0, second.output
    assert "Setup is already complete" in second.output


def test_setup_command_reprompts_after_weak_password(fresh_app, tmp_path):
    target = tmp_path / "setup.db"
    answers = [
        "sqlite",
        str(target),
        "boss@example.com",
        "",
        "Boss User",
        "weakpass",
        "weakpass",
        *(_answers(target)[2:]),
    ]

    result = _run(fresh_app, answers)

    assert result.exit_code == 0, result.output
    assert "password must contain uppercase" in result.output
    assert "Administrator created: boss@example.com" in result.output


def test_setup_command_aborts_when_database_is_unreachable(fresh_app, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")

    result = _run(fresh_app, ["sqlite", str(blocker / "setup.db"), "n"])

    assert result.exit_code == 1
    assert "Try another database?" in result.output


def test_setup_is_registered_on_the_flask_cli(fresh_app):
    assert "setup" in fresh_app.cli.list_commands(click.Context(fresh_app.cli))
