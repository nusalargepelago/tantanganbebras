"""Dashboard HTTP endpoints — admin dashboard payload."""
from __future__ import annotations

from flask_login import login_required

from app.dashboard.services import DashboardService
from app.infra.roles import require_staff
from framework.api import BlueprintFactory, ok

bp = BlueprintFactory("dashboard", __name__, url_prefix="/api/v1/dashboard")


@bp.get("")
@login_required
def admin_dashboard():
    if denied := require_staff():
        return denied

    return ok(DashboardService().admin_payload())


@bp.get("/stats")
@login_required
def admin_dashboard_stats():
    if denied := require_staff():
        return denied

    return ok(DashboardService().stats_payload())
