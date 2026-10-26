"""Terminal twin of the first-run wizard.

The web wizard only answers loopback clients, so a cPanel/Passenger host —
where every request arrives with the real client IP and no local port exists —
has to run setup from a shell. Same service and DTOs as the HTTP path; only
the prompts differ.
"""
from __future__ import annotations

import click

from app.infra.seo import SUPPORTED_LANGS, validate_site_url
from app.infra.setup_dto import AdminCreateIn, BrandIn, DbConfigIn, SetupIn
from app.infra.setup_service import SetupService
from framework.exceptions import DomainException

ENGINES = ("mariadb", "sqlite", "postgresql")
DEFAULT_PORTS = {"mariadb": 3306, "postgresql": 5432}


def _say(key: str) -> str:
    """Error keys are snake_case so the SPA can translate them; a terminal
    only needs them to be readable."""
    return key.replace("_", " ")


def _prompt_db() -> DbConfigIn:
    engine = click.prompt(
        "Database engine", type=click.Choice(ENGINES), default="mariadb"
    )
    if engine == "sqlite":
        path = click.prompt("SQLite path (blank = data/app.db)", default="")
        return DbConfigIn.validate({"engine": engine, "path": path or None})

    return DbConfigIn.validate(
        {
            "engine": engine,
            "host": click.prompt("Host", default="localhost"),
            "port": click.prompt("Port", type=int, default=DEFAULT_PORTS[engine]),
            "database": click.prompt("Database name"),
            "username": click.prompt("Database user"),
            "password": click.prompt("Database password", hide_input=True),
        }
    )


def _prompt_admin() -> AdminCreateIn:
    while True:
        data = {
            "email": click.prompt("Admin email"),
            "username": click.prompt(
                "Admin username (blank = from email)", default=""
            )
            or None,
            "fullName": click.prompt("Full name"),
            "password": click.prompt(
                "Admin password", hide_input=True, confirmation_prompt=True
            ),
        }
        try:
            return AdminCreateIn.validate(data)
        except DomainException as exc:
            click.secho(f"  {_say(exc.message)}", fg="red", err=True)


def _prompt_brand() -> BrandIn:
    name = click.prompt("Brand name", default="Minimals")
    tagline = click.prompt("Tagline (blank = none)", default="")
    description = click.prompt("Description (blank = none)", default="")
    while True:
        site_url = click.prompt("Site URL (blank = none)", default="")
        try:
            validate_site_url(site_url or None)
        except DomainException as exc:
            click.secho(f"  {_say(exc.message)}", fg="red", err=True)
            continue
        break

    return BrandIn(
        name=name,
        tagline=tagline,
        description=description,
        site_url=site_url or None,
    )


def _run_setup() -> None:
    service = SetupService()
    status = service.status()
    if not status["setupRequired"]:
        click.echo(f"Setup is already complete — database {status['activeUrl']}")
        return

    click.echo(f"Current database: {status['activeUrl']}")
    click.echo()

    while True:
        db = _prompt_db()
        try:
            service.test_db(db)
        except DomainException as exc:
            click.secho(f"  {_say(exc.message)}", fg="red", err=True)
            if not click.confirm("Try another database?", default=True):
                raise click.Abort from None
            continue
        click.echo("  connection ok")
        break

    admin = _prompt_admin()
    brand = _prompt_brand()
    lang = click.prompt("Language", type=click.Choice(SUPPORTED_LANGS), default="en")

    result = service.run(SetupIn(db=db, admin=admin, brand=brand, lang=lang))
    click.echo()
    click.echo(f"Administrator created: {result['email']}")
    click.echo("Restart so the running process reloads .env:")
    click.echo("  touch tmp/restart.txt")


@click.group()
def cli() -> None:
    """Minimals management commands."""


@cli.command("setup")
def setup() -> None:
    """Create the schema, administrator and brand. First run only."""
    _run_setup()


def main() -> None:
    from app.create_app import create_app

    app = create_app()
    with app.app_context():
        cli(prog_name="python -m app.cli")


if __name__ == "__main__":
    main()
