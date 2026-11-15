"""Onboarding API — post-register role classification (student or teacher)."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.onboarding.dto import OnboardingStudentIn, OnboardingTeacherIn
from app.onboarding.services import OnboardingService
from framework.api import BlueprintFactory, created, ok
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("onboarding", __name__, url_prefix="/api/v1/onboarding")

_rate_10 = limiter.limit("10/minute")


@bp.get("/status")
@login_required
def onboarding_status():
    return ok(OnboardingService().status(current_user))


@bp.post("/student")
@_rate_10
@login_required
def onboarding_student():
    dto = OnboardingStudentIn.validate(request.get_json(silent=True) or {})
    payload = OnboardingService().classify_student(current_user, dto, actor_id=current_user.id)
    return created(payload)


@bp.post("/teacher")
@_rate_10
@login_required
def onboarding_teacher():
    dto = OnboardingTeacherIn.validate(request.get_json(silent=True) or {})
    payload = OnboardingService().classify_teacher(current_user, dto, actor_id=current_user.id)
    return created(payload)
