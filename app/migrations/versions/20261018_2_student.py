"""student

Revision ID: 20261018_2
Revises: 20261018
Create Date: 2026-10-18 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261018_2"
down_revision: str | None = "20261018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("category", sa.String(length=20), nullable=False, server_default="cub"),
        sa.Column("school", sa.String(length=140), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True, server_default="Indonesia"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Inactive"),
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_students_status", "students", ["status"])
    op.create_index("ix_students_disabled", "students", ["disabled"])
    op.create_index(
        "ix_students_category_status", "students", ["category", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_students_category_status", table_name="students")
    op.drop_index("ix_students_disabled", table_name="students")
    op.drop_index("ix_students_status", table_name="students")
    op.drop_table("students")
