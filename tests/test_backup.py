from __future__ import annotations

import io

BACKUP = "/api/v1/backup"
HEADER = "-- minimals-backup v1"


def _upload(client, script: str, filename: str = "backup.sql"):
    return client.post(
        f"{BACKUP}/import",
        data={"file": (io.BytesIO(script.encode("utf-8")), filename)},
        content_type="multipart/form-data",
    )


def test_export_requires_admin(client, member):
    assert client.get(f"{BACKUP}/export").status_code == 401
    assert member.get(f"{BACKUP}/export").status_code == 403

    payload = {"file": (io.BytesIO(b"COMMIT;"), "backup.sql")}
    assert member.post(f"{BACKUP}/import", data=payload,
                       content_type="multipart/form-data").status_code == 403


def test_export_returns_sql_attachment(app, admin):
    response = admin.get(f"{BACKUP}/export")
    assert response.status_code == 200
    assert response.mimetype == "text/plain"

    disposition = response.headers["Content-Disposition"]
    assert disposition.startswith("attachment")
    assert "minimals-backup-" in disposition

    script = response.get_data(as_text=True)
    assert script.startswith(HEADER)
    assert "BEGIN TRANSACTION;" in script
    assert script.rstrip().endswith("COMMIT;")
    assert 'INSERT INTO "users"' in script
    assert "CREATE TABLE" not in script
    assert "DROP TABLE" not in script


def test_export_is_audited(app, admin):
    from app.infra.audit import AuditLog
    from framework.extensions import db

    response = admin.get(f"{BACKUP}/export")
    assert response.status_code == 200

    with app.app_context():
        actions = [
            row.action
            for row in db.session.query(AuditLog)
            .filter(AuditLog.action == "backup_exported")
            .all()
        ]
    assert actions == ["backup_exported"]


def test_import_requires_admin(app, client, member):
    assert _upload(client, "COMMIT;").status_code == 401
    assert _upload(member, "COMMIT;").status_code == 403


def test_import_requires_file(admin):
    response = admin.post(
        f"{BACKUP}/import", data={"other": "x"}, content_type="multipart/form-data"
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "file_required"}


def test_import_rejects_script_without_statements(admin):
    response = _upload(admin, f"{HEADER}\n-- nothing to do\n")
    assert response.status_code == 400
    assert response.get_json() == {"message": "backup_empty_file"}


def test_import_rejects_forbidden_statement(app, admin):
    from framework.extensions import db

    with app.app_context():
        before = db.session.execute(db.text("SELECT COUNT(*) FROM todos")).scalar()

    response = _upload(admin, "BEGIN TRANSACTION;\nDROP TABLE todos;\nCOMMIT;")
    assert response.status_code == 400
    assert response.get_json() == {"message": "backup_statement_not_allowed"}

    with app.app_context():
        after = db.session.execute(db.text("SELECT COUNT(*) FROM todos")).scalar()
    assert after == before


def test_import_rejects_unknown_table(admin):
    response = _upload(admin, 'DELETE FROM "sqlite_master";')
    assert response.status_code == 400
    assert response.get_json() == {"message": "backup_statement_not_allowed"}


def test_import_rejects_statement_after_semicolon(admin):
    script = 'DELETE FROM "todos";\nPRAGMA foreign_keys = OFF;'
    response = _upload(admin, script)
    assert response.status_code == 400
    assert response.get_json() == {"message": "backup_statement_not_allowed"}


def test_round_trip_preserves_quotes_and_sql_in_text(app, admin):
    title = "'; DROP TABLE users; -- ? :colon \\_(?)_/"
    created = admin.post("/api/v1/todos", json={"title": title})
    assert created.status_code == 201, created.get_json()
    todo_id = created.get_json()["id"]

    script = admin.get(f"{BACKUP}/export").get_data(as_text=True)
    assert admin.delete(f"/api/v1/todos/{todo_id}").status_code == 204
    assert _upload(admin, script).status_code == 200

    restored = admin.get(f"/api/v1/todos/{todo_id}")
    assert restored.status_code == 200
    assert restored.get_json()["title"] == title


def test_round_trip_restores_deleted_rows(app, admin):
    created = admin.post("/api/v1/todos", json={"title": "backup marker"})
    assert created.status_code == 201, created.get_json()
    todo_id = created.get_json()["id"]

    exported = admin.get(f"{BACKUP}/export")
    assert exported.status_code == 200
    script = exported.get_data(as_text=True)

    assert admin.delete(f"/api/v1/todos/{todo_id}").status_code == 204
    assert admin.get("/api/v1/todos").get_json()["total"] == 0

    restored = _upload(admin, script)
    assert restored.status_code == 200, restored.get_json()
    body = restored.get_json()
    assert body["tables"] > 10
    assert body["rows"] > 0

    titles = [row["title"] for row in admin.get("/api/v1/todos").get_json()["items"]]
    assert "backup marker" in titles


def test_round_trip_keeps_identity_and_types(app, admin):
    created = admin.post(
        "/api/v1/todos", json={"title": "typed marker", "completed": True}
    )
    assert created.status_code == 201, created.get_json()
    todo_id = created.get_json()["id"]

    script = admin.get(f"{BACKUP}/export").get_data(as_text=True)
    assert admin.delete(f"/api/v1/todos/{todo_id}").status_code == 204
    assert _upload(admin, script).status_code == 200

    restored = admin.get(f"/api/v1/todos/{todo_id}")
    assert restored.status_code == 200
    body = restored.get_json()
    assert body["title"] == "typed marker"
    assert body["completed"] is True
    assert body["id"] == todo_id


def test_import_is_audited(app, admin):
    from app.infra.audit import AuditLog
    from framework.extensions import db

    script = admin.get(f"{BACKUP}/export").get_data(as_text=True)
    response = _upload(admin, script)
    assert response.status_code == 200

    with app.app_context():
        rows = (
            db.session.query(AuditLog)
            .filter(AuditLog.action == "backup_restored")
            .all()
        )
    assert len(rows) == 1
    assert rows[0].details["tables"] > 10
