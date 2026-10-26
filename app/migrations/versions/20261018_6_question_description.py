"""question description

Revision ID: 20261018_6
Revises: 20261018_5
Create Date: 2026-10-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261018_6"
down_revision: str | None = "20261018_5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "description")
