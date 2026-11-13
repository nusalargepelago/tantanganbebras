"""Brand endpoints — global white-label settings."""
from __future__ import annotations

from flask import request
from flask_login import login_required

from app.infra.brand_dto import BrandLogoIn
from app.infra.brand_service import BrandService
from framework.api import BlueprintFactory, ok
from framework.auth.helpers import require_role

bp = BlueprintFactory("brand", __name__, url_prefix="/api/v1/brand")


@bp.put("/logo")
@login_required
def update_logo():
    if denied := require_role("admin"):
        return denied
    dto = BrandLogoIn.validate(request.get_json(silent=True) or {})
    return ok({"logoUrl": BrandService().save_logo(dto.logo_url)})


__all__ = ["bp"]
