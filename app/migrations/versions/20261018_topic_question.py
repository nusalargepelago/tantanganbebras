"""topic & question

Revision ID: 20261018
Revises: 0001
Create Date: 2026-10-18 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261018"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=140), unique=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "creator_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=140), unique=True, nullable=False),
        sa.Column("question_code", sa.String(length=40), nullable=False, server_default="Mini Challenge"),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=20), nullable=False, server_default="Multiple Choice"),
        sa.Column("option_a", sa.Text(), nullable=True),
        sa.Column("option_b", sa.Text(), nullable=True),
        sa.Column("option_c", sa.Text(), nullable=True),
        sa.Column("option_d", sa.Text(), nullable=True),
        sa.Column("reference_answer", sa.Text(), nullable=True),
        sa.Column("correct_answer", sa.String(length=8), nullable=True),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("difficulty_level", sa.String(length=20), nullable=False, server_default="Easy"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Active"),
        sa.Column(
            "creator_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "topic_id",
            sa.String(length=140),
            sa.ForeignKey("topics.name", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_topics_category", "topics", ["category"])
    op.create_index("ix_topics_category_idx", "topics", ["category", "idx"])
    op.create_index("ix_questions_category", "questions", ["category"])
    op.create_index("ix_questions_topic_id", "questions", ["topic_id"])
    op.create_index("ix_questions_disabled", "questions", ["disabled"])
    op.create_index("ix_questions_category_status", "questions", ["category", "status"])
    op.create_index(
        "ix_questions_category_difficulty_level", "questions", ["category", "difficulty_level"]
    )


def downgrade() -> None:
    op.drop_index("ix_questions_category_difficulty_level", table_name="questions")
    op.drop_index("ix_questions_category_status", table_name="questions")
    op.drop_index("ix_questions_disabled", table_name="questions")
    op.drop_index("ix_questions_topic_id", table_name="questions")
    op.drop_index("ix_questions_category", table_name="questions")
    op.drop_index("ix_topics_category_idx", table_name="topics")
    op.drop_index("ix_topics_category", table_name="topics")
    op.drop_table("questions")
    op.drop_table("topics")
