"""First-run setup blueprint — database configuration and administrator creation."""
from __future__ import annotations

import ipaddress

from flask import request

from app.infra.setup_dto import DbConfigIn, SetupIn
from app.infra.setup_service import SetupService
from framework.api import BlueprintFactory, created, error, ok

bp = BlueprintFactory("setup", __name__, url_prefix="/api/v1/setup")


def _client_ip(value: str | None):
    try:
        return ipaddress.ip_address(value) if value else None
    except ValueError:
        return None


def _is_local(addr) -> bool:
    return addr is not None and addr.is_loopback


def _client_is_loopback() -> bool:
    """Whether every hop to this client is loopback.

    Every hop must be loopback: the raw socket peer (pre-ProxyFix) so a
    forged X-Forwarded-For cannot spoof locality, the effective address,
    and the last forwarded entry. A private-network client (e.g. another
    VM in the same cloud VPC) is rejected — it could otherwise create an
    admin and rewrite DATABASE_URL.
    """
    peer = _client_ip(request.environ.get("RAW_REMOTE_ADDR") or request.remote_addr)
    if not _is_local(peer):
        return False
    if not _is_local(_client_ip(request.remote_addr)):
        return False
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded and not _is_local(_client_ip(forwarded.split(",")[-1].strip())):
        return False
    return True


def _deny_public_client():
    """Setup wizard is only reachable from the host itself."""
    if not _client_is_loopback():
        return error("forbidden", 403)
    return None


@bp.get("/status")
def status():
    return ok(SetupService().status(include_details=_client_is_loopback()))


@bp.post("/db-test")
def db_test():
    if denied := _deny_public_client():
        return denied
    dto = DbConfigIn.validate(request.get_json(silent=True) or {})
    return ok({"ok": True, "engine": dto.engine, "url": SetupService().test_db(dto)})


@bp.post("")
def setup():
    if denied := _deny_public_client():
        return denied
    dto = SetupIn.validate(request.get_json(silent=True) or {})
    return created(SetupService().run(dto))


__all__ = ["bp"]
