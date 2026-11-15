"""master schools get a city (kabupaten/kota) and students/teachers inherit it

Revision ID: 20261114_9
Revises: 20261114_8
Create Date: 2026-11-14 00:00:00.000000

Schools now own a city (kabupaten/kota); students and teachers inherit their
city from their school through the schools table. The free-text city columns
on students/teachers are dropped. The country is always "Indonesia".
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "20261114_9"
down_revision: str | None = "20261114_8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHOOL_CITY = {
    "SMA Katolik Kesuma Mataram": "Kota Mataram",
    "SMP Katolik Kesuma Mataram": "Kota Mataram",
    "SD Negeri 8 Sokong": "Kabupaten Lombok Utara",
    "SMPN 4 Gerung": "Kabupaten Lombok Barat",
    "MI NW Dasan Tengak": "Kabupaten Lombok Tengah",
    "SMPN 1 Pemenang": "Kabupaten Lombok Utara",
    "MTs Nurul Islam Sekarbela": "Kota Mataram",
    "SDK St. Antonius Ampenan": "Kota Mataram",
    "SD Negeri 3 Sokong": "Kabupaten Lombok Utara",
    "SMAN 4 Mataram": "Kota Mataram",
    "SDK St. Antonius Cakranegara": "Kota Mataram",
    "SDN 36 Mataram": "Kota Mataram",
    "SDN Kwang Rase": "Kabupaten Lombok Tengah",
    "SMP Islam Riyadlul Ulum Mentokan": "Kabupaten Lombok Barat",
    "SMPN 4 Mataram": "Kota Mataram",
    "MI Nurul Islam": "Kota Mataram",
    "SMAN 7 Mataram": "Kota Mataram",
    "SDN 31 Mataram": "Kota Mataram",
    "SDN 2 Mataram": "Kota Mataram",
    "SDN 40 Mataram": "Kota Mataram",
    "SMPN 19 Mataram": "Kota Mataram",
    "SDN 19 Mataram": "Kota Mataram",
    "SMPN 1 Mataram": "Kota Mataram",
    "SDN 1 Sila": "Kabupaten Lombok Tengah",
    "SMPN 2 Semarang": "Kabupaten Semarang",
    "SMPN 1 Denpasar": "Kota Denpasar",
    "SMPN 4 Pasrepan": "Kabupaten Pasuruan",
    "MAN 1 Banda Aceh": "Kota Banda Aceh",
    "SD Negeri 33 Mataram": "Kota Mataram",
    "Demo": "Kota Mataram",
}


def upgrade() -> None:
    bind = op.get_bind()
    ctx = op.get_context()

    # The batch rebuilds below DROP `schools` / `students` / `teachers`
    # while other tables still reference them; SQLite only honors
    # PRAGMA foreign_keys outside a transaction, so drop into autocommit
    # to flip it off. It stays off for the rest of this connection;
    # re-enabled (and verified) at the end.
    with ctx.autocommit_block():
        bind.exec_driver_sql("PRAGMA foreign_keys=OFF")
    try:
        # 1) Add the nullable column first (backfilled before the constraint).
        #    Idempotent: skip when a previous attempt already added it.
        inspector = sa.inspect(bind)
        schools_cols = {c["name"] for c in inspector.get_columns("schools")}
        if "city_id" not in schools_cols:
            with op.batch_alter_table("schools") as batch:
                batch.add_column(sa.Column("city_id", sa.String(length=36), nullable=True))

        # 2) Resolve city ids by name.
        cities = {
            name: city_id
            for city_id, name in bind.execute(text("SELECT id, name FROM cities"))
        }
        missing = sorted({city for city in SCHOOL_CITY.values() if city not in cities})
        if missing:
            raise RuntimeError(f"cities not seeded: {', '.join(missing)}")

        # 3) Backfill per canonical school (only rows still missing a city).
        school_rows = bind.execute(
            text("SELECT id, name FROM schools WHERE city_id IS NULL")
        ).fetchall()
        unresolved = []
        for school_id, school_name in school_rows:
            city_name = SCHOOL_CITY.get(school_name)
            if not city_name:
                unresolved.append(school_name)
                continue
            bind.execute(
                text("UPDATE schools SET city_id = :cid WHERE id = :sid"),
                {"cid": cities[city_name], "sid": school_id},
            )
        if unresolved:
            raise RuntimeError(f"schools without a city mapping: {', '.join(unresolved)}")

        # 4) Enforce NOT NULL + FK.
        schools_fks = {
            fk.get("name") for fk in sa.inspect(bind).get_foreign_keys("schools")
        }
        with op.batch_alter_table("schools") as batch:
            batch.alter_column(
                "city_id", existing_type=sa.String(length=36), nullable=False
            )
            if "fk_schools_city_id" not in schools_fks:
                batch.create_foreign_key("fk_schools_city_id", "cities", ["city_id"], ["id"])

        # 5) City now inherits from the school — drop the per-row columns.
        for table in ("students", "teachers"):
            inspector = sa.inspect(bind)
            cols = {c["name"] for c in inspector.get_columns(table)}
            fks = {fk.get("name") for fk in inspector.get_foreign_keys(table)}
            if "city_id" not in cols and f"fk_{table}_city_id" not in fks:
                continue
            with op.batch_alter_table(table) as batch:
                if f"fk_{table}_city_id" in fks:
                    batch.drop_constraint(f"fk_{table}_city_id", type_="foreignkey")
                if "city_id" in cols:
                    batch.drop_column("city_id")
    finally:
        with ctx.autocommit_block():
            bind.exec_driver_sql("PRAGMA foreign_keys=ON")

    # A silent orphan is worse than a failed migration — surface it.
    violations = bind.execute(text("PRAGMA foreign_key_check")).fetchall()
    if violations:
        raise RuntimeError(
            f"foreign key violations after 20261114_9: {violations[:5]}"
        )


def downgrade() -> None:
    bind = op.get_bind()
    ctx = op.get_context()

    with ctx.autocommit_block():
        bind.exec_driver_sql("PRAGMA foreign_keys=OFF")
    try:
        for table in ("students", "teachers"):
            inspector = sa.inspect(bind)
            cols = {c["name"] for c in inspector.get_columns(table)}
            if "city_id" in cols:
                continue
            with op.batch_alter_table(table) as batch:
                batch.add_column(sa.Column("city_id", sa.String(length=36), nullable=True))
                batch.create_foreign_key(
                    f"fk_{table}_city_id", "cities", ["city_id"], ["id"]
                )

        bind.execute(
            text(
                "UPDATE students SET city_id = (SELECT city_id FROM schools WHERE schools.id = students.school_id)"
                " WHERE students.city_id IS NULL"
            )
        )
        bind.execute(
            text(
                "UPDATE teachers SET city_id = (SELECT city_id FROM schools WHERE schools.id = teachers.school_id)"
                " WHERE teachers.city_id IS NULL"
            )
        )

        inspector = sa.inspect(bind)
        schools_cols = {c["name"] for c in inspector.get_columns("schools")}
        schools_fks = {fk.get("name") for fk in inspector.get_foreign_keys("schools")}
        if "city_id" in schools_cols:
            with op.batch_alter_table("schools") as batch:
                if "fk_schools_city_id" in schools_fks:
                    batch.drop_constraint("fk_schools_city_id", type_="foreignkey")
                batch.drop_column("city_id")
    finally:
        with ctx.autocommit_block():
            bind.exec_driver_sql("PRAGMA foreign_keys=ON")
