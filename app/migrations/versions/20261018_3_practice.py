"""practice

Revision ID: 20261018_3
Revises: 20261018_2
Create Date: 2026-10-18 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261018_3"
down_revision: str | None = "20261018_2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "practices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=140), unique=True, nullable=False),
        sa.Column(
            "student_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=20), nullable=False, server_default="cub"),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("time_limit", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "practice_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "practice_id",
            sa.String(length=140),
            sa.ForeignKey("practices.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.String(length=140),
            sa.ForeignKey("questions.name", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("shuffled_idx", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("practice_id", "question_id", name="uq_practice_question"),
    )
    op.create_table(
        "practice_before_shuffle",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "practice_id",
            sa.String(length=140),
            sa.ForeignKey("practices.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.String(length=140),
            sa.ForeignKey("questions.name", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("original_idx", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "practice_answers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "practice_id",
            sa.String(length=140),
            sa.ForeignKey("practices.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.String(length=140),
            sa.ForeignKey("questions.name", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("answer", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("practice_id", "question_id", name="uq_practice_answer"),
    )
    op.create_table(
        "practice_answer_temps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "practice_id",
            sa.String(length=140),
            sa.ForeignKey("practices.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.String(length=140),
            sa.ForeignKey("questions.name", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("answer", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("practice_id", "question_id", name="uq_practice_answer_temp"),
    )
    op.create_index("ix_practices_student_id", "practices", ["student_id"])
    op.create_index("ix_practices_category", "practices", ["category"])
    op.create_index("ix_practices_created_at", "practices", ["created_at"])
    op.create_index("ix_practice_questions_practice_id", "practice_questions", ["practice_id"])
    op.create_index(
        "ix_practice_questions_shuffled", "practice_questions", ["practice_id", "shuffled_idx"]
    )
    op.create_index("ix_practice_before_shuffle_practice_id", "practice_before_shuffle", ["practice_id"])
    op.create_index("ix_practice_answers_practice_id", "practice_answers", ["practice_id"])
    op.create_index("ix_practice_answer_temps_practice_id", "practice_answer_temps", ["practice_id"])


def downgrade() -> None:
    op.drop_index("ix_practice_answer_temps_practice_id", table_name="practice_answer_temps")
    op.drop_index("ix_practice_answers_practice_id", table_name="practice_answers")
    op.drop_index("ix_practice_before_shuffle_practice_id", table_name="practice_before_shuffle")
    op.drop_index("ix_practice_questions_shuffled", table_name="practice_questions")
    op.drop_index("ix_practice_questions_practice_id", table_name="practice_questions")
    op.drop_index("ix_practices_created_at", table_name="practices")
    op.drop_index("ix_practices_category", table_name="practices")
    op.drop_index("ix_practices_student_id", table_name="practices")
    op.drop_table("practice_answer_temps")
    op.drop_table("practice_answers")
    op.drop_table("practice_before_shuffle")
    op.drop_table("practice_questions")
    op.drop_table("practices")
