"""teacher

Revision ID: 20261114_7
Revises: 20261018_6
Create Date: 2026-11-14 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261114_7"
down_revision: str | None = "20261018_6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teachers",
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("school", sa.String(length=140), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True, server_default="Indonesia"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("teachers")
