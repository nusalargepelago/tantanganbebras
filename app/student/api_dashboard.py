"""Student dashboard HTTP endpoint — student-session dashboard payload."""
from __future__ import annotations

from flask_login import current_user, login_required

from app.dashboard.services import DashboardService
from framework.api import BlueprintFactory, ok

bp = BlueprintFactory("student_dashboard", __name__, url_prefix="/api/v1/student")


@bp.get("/dashboard")
@login_required
def student_dashboard():
    return ok(DashboardService().student_payload(current_user.id))
