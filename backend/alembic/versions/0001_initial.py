"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-05 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "assessment_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("scale_type", sa.Enum("HAMD", "HAMA", "PHQ9", name="scaletype"), nullable=False),
        sa.Column("audio_path", sa.String(length=512), nullable=False),
        sa.Column("audio_original_name", sa.String(length=255), nullable=False),
        sa.Column("audio_mime_type", sa.String(length=128), nullable=True),
        sa.Column("audio_size", sa.Integer(), nullable=False),
        sa.Column("asr_text", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", name="taskstatus"), nullable=False),
        sa.Column("stage", sa.Enum("ASR", "QC", name="taskstage"), nullable=True),
        sa.Column("review_status", sa.Enum("UNREVIEWED", "REVIEWED", name="reviewstatus"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assessment_tasks_id"), "assessment_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_assessment_tasks_owner_id"), "assessment_tasks", ["owner_id"], unique=False)
    op.create_index(op.f("ix_assessment_tasks_scale_type"), "assessment_tasks", ["scale_type"], unique=False)

    op.create_table(
        "qc_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("doctor_score", sa.Float(), nullable=True),
        sa.Column("ai_score", sa.Float(), nullable=True),
        sa.Column("scoring_basis", sa.Text(), nullable=True),
        sa.Column("evidence_analysis", sa.Text(), nullable=True),
        sa.Column("error_reason", sa.Text(), nullable=True),
        sa.Column("optimization_suggestion", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["assessment_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index(op.f("ix_qc_results_id"), "qc_results", ["id"], unique=False)

    op.create_table(
        "review_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("reviewed_score", sa.Float(), nullable=False),
        sa.Column("review_reason", sa.Text(), nullable=False),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["assessment_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index(op.f("ix_review_records_id"), "review_records", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_review_records_id"), table_name="review_records")
    op.drop_table("review_records")
    op.drop_index(op.f("ix_qc_results_id"), table_name="qc_results")
    op.drop_table("qc_results")
    op.drop_index(op.f("ix_assessment_tasks_scale_type"), table_name="assessment_tasks")
    op.drop_index(op.f("ix_assessment_tasks_owner_id"), table_name="assessment_tasks")
    op.drop_index(op.f("ix_assessment_tasks_id"), table_name="assessment_tasks")
    op.drop_table("assessment_tasks")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

