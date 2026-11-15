"""First-run setup service — status detection, connection test, and bootstrap."""
from __future__ import annotations

import ipaddress
import logging
import socket
import threading
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.auth.models import MEMBER_ROLE, Role
from app.auth.services import AuthService
from app.config import BASE_DIR
from app.infra import db_bootstrap
from app.infra.seo import (
    SUPPORTED_LANGS,
    save_app_lang,
    save_brand,
    validate_site_url,
)
from app.infra.setup_dto import AdminCreateIn, BrandIn, DbConfigIn, SetupIn
from framework.exceptions import Conflict, DomainException, ValidationFailed
from framework.extensions import db

logger = logging.getLogger(__name__)

_setup_lock = threading.Lock()

MIGRATIONS_DIR = str(BASE_DIR / "migrations")


def _deny_metadata_host(url: str) -> None:
    """Refuse DB targets that resolve to link-local addresses (cloud metadata)."""
    host = urlsplit(url).hostname
    if not host:
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return
    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if addr.is_link_local:
            raise ValidationFailed("unsupported_host")


def _active_engine_url() -> str:
    try:
        return str(db.engine.url)
    except Exception:
        return db_bootstrap.default_sqlite_url()


def _has_schema(url: str) -> bool:
    engine = None
    try:
        engine = db_bootstrap._engine_of(url)
        return "users" in inspect(engine).get_table_names()
    except Exception:
        return False
    finally:
        if engine is not None:
            engine.dispose()


def _user_count(url: str) -> int:
    if not _has_schema(url):
        return 0
    engine = None
    try:
        engine = db_bootstrap._engine_of(url)
        with engine.connect() as conn:
            return int(conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0)
    except Exception:
        return 0
    finally:
        if engine is not None:
            engine.dispose()


def _engine_name(url: str) -> str:
    return url.split(":", 1)[0].split("+")[0]


def _mask_password(url: str) -> str:
    parts = urlsplit(url)
    if parts.password:
        netloc = parts.netloc.replace(f":{parts.password}@", ":*****@")
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    return url


def _requires_restart(active_url: str, target_url: str) -> bool:
    a, t = urlsplit(active_url), urlsplit(target_url)
    return (a.scheme, a.netloc, a.path) != (t.scheme, t.netloc, t.path)


def _build_url(cfg: DbConfigIn) -> str:
    return db_bootstrap.build_url(
        cfg.engine,
        host=cfg.host,
        port=cfg.port,
        database=cfg.database,
        username=cfg.username,
        password=cfg.password,
        path=cfg.path,
    )


class SetupService:
    """Owns every rule of the first-run wizard; the blueprint only translates HTTP."""

    def status(self, *, include_details: bool = False) -> dict:
        url = _active_engine_url()
        details = {}
        if include_details:
            details = {
                "activeEngine": _engine_name(url),
                "activeUrl": _mask_password(url),
            }
        if not _has_schema(url):
            return {"setupRequired": True, "reason": "no_schema", **details}
        if _user_count(url) == 0:
            return {"setupRequired": True, "reason": "no_users", **details}
        return {"setupRequired": False, "reason": None, **details}

    def test_db(self, cfg: DbConfigIn) -> str:
        if not self.status()["setupRequired"]:
            raise Conflict("setup_already_complete")

        url = _build_url(cfg)
        _deny_metadata_host(url)
        try:
            db_bootstrap.test_connection(url)
        except Exception as exc:
            logger.info("db-test failed for %s: %s", cfg.engine, exc)
            raise ValidationFailed(db_bootstrap.db_error_key(exc)) from exc
        return _mask_password(url)

    def run(self, dto: SetupIn) -> dict:
        with _setup_lock:
            if not self.status()["setupRequired"]:
                raise Conflict("setup_already_complete")

            brand = dto.brand or BrandIn()
            validate_site_url(brand.site_url)

            lang = (dto.lang or "").strip().lower() or "en"
            if lang not in SUPPORTED_LANGS:
                raise ValidationFailed("unsupported_lang")

            url = _build_url(dto.db)
            _deny_metadata_host(url)
            try:
                db_bootstrap.test_connection(url)
            except Exception as exc:
                logger.info(
                    "setup db unreachable for %s: %s",
                    _mask_password(url),
                    exc,
                )
                raise ValidationFailed(db_bootstrap.db_error_key(exc)) from exc

            active_url = _active_engine_url()
            if url != active_url:
                try:
                    db_bootstrap.write_database_url_to_env(url)
                except Exception:
                    logger.exception("setup env write failed")
                    raise DomainException(
                        "setup_env_write_failed", status_code=500
                    ) from None

            try:
                db_bootstrap.migrate_to(url, MIGRATIONS_DIR)
            except Exception:
                logger.exception("setup migration failed")
                raise DomainException("setup_migration_failed", status_code=500) from None

            try:
                admin_id = _seed_initial(url, dto.admin, brand, lang)
            except Exception:
                logger.exception("setup seeding/admin failed")
                raise DomainException("setup_admin_failed", status_code=500) from None

            # The wizard already migrated and seeded through its own engine, so
            # the new database is complete. Point the live engine at it instead
            # of asking the operator to restart. If this fails the application
            # keeps serving the previous database and the .env write above means
            # a restart still lands on the new one.
            if _requires_restart(active_url, url):
                try:
                    db_bootstrap.repoint_engine(url)
                except Exception:
                    logger.exception("setup engine re-point failed")
                    raise DomainException(
                        "setup_repoint_failed", status_code=500
                    ) from None

            return {
                "adminId": admin_id,
                "email": dto.admin.email,
                "restartRequired": False,
            }


def _seed_initial(url: str, admin: AdminCreateIn, brand: BrandIn, lang: str) -> str:
    engine = db_bootstrap._engine_of(url)
    try:
        with Session(engine) as session:
            member = session.scalars(select(Role).where(Role.name == MEMBER_ROLE)).first()
            if member is None:
                member = Role(name=MEMBER_ROLE)
                session.add(member)
                session.flush()

            admin_user = AuthService.build_user(
                username=admin.username or admin.email.split("@")[0],
                email=admin.email,
                full_name=admin.full_name,
                password=admin.password,
                app_role="admin",
            )
            admin_user.roles.append(member)
            session.add(admin_user)
            save_brand(session, brand.model_dump(by_alias=True))
            save_app_lang(session, lang)
            session.commit()
            return admin_user.id
    finally:
        engine.dispose()


__all__ = ["SetupService"]
