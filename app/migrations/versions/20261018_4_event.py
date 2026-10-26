"""event

Revision ID: 20261018_4
Revises: 20261018_3
Create Date: 2026-10-18 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261018_4"
down_revision: str | None = "20261018_3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=140), unique=True, nullable=False),
        sa.Column("event_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("time_limit", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("event_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "creator_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
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
    op.create_table(
        "event_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(length=140),
            sa.ForeignKey("events.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.String(length=140),
            sa.ForeignKey("questions.name", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("idx", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("event_id", "question_id", name="uq_event_question"),
    )
    op.create_table(
        "event_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=140), unique=True, nullable=False),
        sa.Column(
            "student_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.String(length=140),
            sa.ForeignKey("events.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("time_limit", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "event_attempt_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "event_attempt_id",
            sa.String(length=140),
            sa.ForeignKey("event_attempts.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.String(length=140),
            sa.ForeignKey("questions.name", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("idx", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("event_attempt_id", "question_id", name="uq_event_attempt_question"),
    )
    op.create_table(
        "event_attempt_answers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "event_attempt_question_id",
            sa.String(length=36),
            sa.ForeignKey("event_attempt_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answer", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "event_attempt_answer_temps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "event_attempt_id",
            sa.String(length=140),
            sa.ForeignKey("event_attempts.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_attempt_question_id",
            sa.String(length=36),
            sa.ForeignKey("event_attempt_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answer", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "event_attempt_id", "event_attempt_question_id", name="uq_event_attempt_temp"
        ),
    )
    op.create_index("ix_events_category", "events", ["category"])
    op.create_index("ix_events_event_deadline", "events", ["event_deadline"])
    op.create_index("ix_events_published", "events", ["published"])
    op.create_index("ix_events_disabled", "events", ["disabled"])
    op.create_index("ix_event_questions_event_id", "event_questions", ["event_id"])
    op.create_index("ix_event_attempts_student_id", "event_attempts", ["student_id"])
    op.create_index("ix_event_attempts_event_id", "event_attempts", ["event_id"])
    op.create_index("ix_event_attempts_created_at", "event_attempts", ["created_at"])
    op.create_index(
        "ix_event_attempt_questions_event_attempt_id", "event_attempt_questions", ["event_attempt_id"]
    )
    op.create_index(
        "ix_event_attempt_questions_idx", "event_attempt_questions", ["event_attempt_id", "idx"]
    )
    op.create_index(
        "ix_event_attempt_answers_event_attempt_question_id",
        "event_attempt_answers",
        ["event_attempt_question_id"],
    )
    op.create_index(
        "ix_event_attempt_answer_temps_event_attempt_id",
        "event_attempt_answer_temps",
        ["event_attempt_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_attempt_answer_temps_event_attempt_id",
        table_name="event_attempt_answer_temps",
    )
    op.drop_index(
        "ix_event_attempt_answers_event_attempt_question_id",
        table_name="event_attempt_answers",
    )
    op.drop_index("ix_event_attempt_questions_idx", table_name="event_attempt_questions")
    op.drop_index(
        "ix_event_attempt_questions_event_attempt_id", table_name="event_attempt_questions"
    )
    op.drop_index("ix_event_attempts_created_at", table_name="event_attempts")
    op.drop_index("ix_event_attempts_event_id", table_name="event_attempts")
    op.drop_index("ix_event_attempts_student_id", table_name="event_attempts")
    op.drop_index("ix_event_questions_event_id", table_name="event_questions")
    op.drop_index("ix_events_disabled", table_name="events")
    op.drop_index("ix_events_published", table_name="events")
    op.drop_index("ix_events_event_deadline", table_name="events")
    op.drop_index("ix_events_category", table_name="events")
    op.drop_table("event_attempt_answer_temps")
    op.drop_table("event_attempt_answers")
    op.drop_table("event_attempt_questions")
    op.drop_table("event_attempts")
    op.drop_table("event_questions")
    op.drop_table("events")
