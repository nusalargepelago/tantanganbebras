"""Student import HTTP endpoints — XLSX bulk upsert and template download."""
from __future__ import annotations

from io import BytesIO

from flask import request, send_file
from flask_login import current_user, login_required

from app.infra.roles import require_staff
from app.student.services import StudentService, build_template
from framework.api import BlueprintFactory, error, ok
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("student_import", __name__, url_prefix="/api/v1/student")

_rate_5 = limiter.limit("5/minute")


@bp.post("/import")
@_rate_5
@login_required
def import_students():
    if denied := require_staff():
        return denied

    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return error("file_required", 400)

    service = StudentService()
    rows, file_error = service.parse_workbook(upload.stream)
    if file_error is not None:
        return ok({"inserted": 0, "updated": 0, "errors": [file_error]})

    summary = service.import_rows(rows, actor_id=current_user.id)
    return ok(summary)


@bp.get("/import-template")
@login_required
def import_template():
    if denied := require_staff():
        return denied

    data = build_template()
    return send_file(
        BytesIO(data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="student-import-template.xlsx",
    )
