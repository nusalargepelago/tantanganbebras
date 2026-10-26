"""Database backup — full-schema SQL dump and admin-only restore."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from flask import Response, current_app, request
from flask_login import current_user, login_required
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.infra.audit import log as audit_log
from framework.api import BlueprintFactory, ok
from framework.auth.helpers import require_role
from framework.exceptions import InvalidOperation, ValidationFailed
from framework.extensions import db
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("backup", __name__, url_prefix="/api/v1/backup")

HEADER = "-- minimals-backup v1"
_rate_2 = limiter.limit("2/minute")
_TARGET = re.compile(r'^(DELETE FROM|INSERT INTO) "([A-Za-z_][A-Za-z0-9_]*)"')


def _tables() -> list:
    existing = set(inspect(db.engine).get_table_names())
    return [table for table in db.metadata.sorted_tables if table.name in existing]


def _literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, bytes | bytearray | memoryview):
        return "X'" + bytes(value).hex() + "'"
    return "'" + str(value).replace("'", "''") + "'"


def build_dump() -> tuple[str, int, int]:
    if db.engine.dialect.name != "sqlite":
        raise InvalidOperation("backup_unsupported_database")
    tables = _tables()
    lines = [HEADER, "BEGIN TRANSACTION;"]
    rows = 0
    with db.engine.connect() as connection:
        for table in reversed(tables):
            lines.append(f'DELETE FROM "{table.name}";')
        for table in tables:
            result = connection.execute(text(f'SELECT * FROM "{table.name}"'))
            columns = list(result.keys())
            if not columns:
                continue
            header = ", ".join(f'"{column}"' for column in columns)
            for row in result:
                rows += 1
                values = ", ".join(_literal(value) for value in row)
                lines.append(f'INSERT INTO "{table.name}" ({header}) VALUES ({values});')
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n", len(tables), rows


def split_statements(script: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    quoted = False
    index = 0
    length = len(script)
    while index < length:
        char = script[index]
        if quoted:
            buffer.append(char)
            if char == "'":
                if index + 1 < length and script[index + 1] == "'":
                    buffer.append("'")
                    index += 2
                    continue
                quoted = False
            index += 1
            continue
        if char == "-" and index + 1 < length and script[index + 1] == "-":
            index = script.find("\n", index)
            if index < 0:
                break
            continue
        if char == "'":
            quoted = True
            buffer.append(char)
        elif char == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
        else:
            buffer.append(char)
        index += 1
    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def _plan(statements: list[str]) -> tuple[list[str], int, int]:
    allowed = {table.name for table in db.metadata.sorted_tables}
    plan: list[str] = []
    tables: set[str] = set()
    inserts = 0
    for statement in statements:
        head = statement.lstrip()
        if head.startswith(("BEGIN TRANSACTION", "COMMIT")):
            continue
        match = _TARGET.match(head)
        if match is None or match.group(2) not in allowed:
            current_app.logger.warning("backup rejected statement: %.160s", head)
            raise ValidationFailed("backup_statement_not_allowed")
        tables.add(match.group(2))
        if match.group(1) == "INSERT INTO":
            inserts += 1
        plan.append(statement)
    if not plan:
        raise ValidationFailed("backup_empty_file")
    return plan, len(tables), inserts


def _restore(plan: list[str]) -> None:
    try:
        connection = db.session.connection()
        for statement in plan:
            connection.exec_driver_sql(statement)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.warning("backup restore failed: %s", exc)
        raise ValidationFailed("backup_restore_failed") from exc


@bp.get("/export")
@login_required
def export_backup():
    if denied := require_role("admin"):
        return denied

    script, tables, rows = build_dump()
    audit_log(
        "backup_exported",
        user_id=current_user.id,
        resource="backup/export",
        details={"tables": tables, "rows": rows},
    )
    db.session.commit()

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    response = Response(script, mimetype="text/plain; charset=utf-8")
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"minimals-backup-{stamp}.sql"
    )
    return response


@bp.post("/import")
@_rate_2
@login_required
def import_backup():
    if denied := require_role("admin"):
        return denied

    upload = (request.files or {}).get("file")
    if upload is None or not upload.filename:
        raise ValidationFailed("file_required")
    script = upload.read().decode("utf-8", errors="replace")
    statements = split_statements(script)
    if not statements:
        raise ValidationFailed("backup_empty_file")
    plan, tables, rows = _plan(statements)
    _restore(plan)

    audit_log(
        "backup_restored",
        user_id=current_user.id,
        resource="backup/import",
        details={"tables": tables, "rows": rows},
    )
    db.session.commit()
    return ok({"tables": tables, "rows": rows})


__all__ = ["HEADER", "bp", "build_dump", "split_statements"]
