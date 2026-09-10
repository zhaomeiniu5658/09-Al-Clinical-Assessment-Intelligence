"""add optional doctor test file to assessment tasks

Revision ID: 0007_dify_workflow_doctor_test
Revises: 0006_qc_item_results
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0007_dify_workflow_doctor_test"
down_revision: str | None = "0006_qc_item_results"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("assessment_tasks", sa.Column("doctor_test_path", sa.String(length=512), nullable=True))
    op.add_column("assessment_tasks", sa.Column("doctor_test_original_name", sa.String(length=255), nullable=True))
    op.add_column("assessment_tasks", sa.Column("doctor_test_mime_type", sa.String(length=128), nullable=True))
    op.add_column("assessment_tasks", sa.Column("doctor_test_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("assessment_tasks", "doctor_test_size")
    op.drop_column("assessment_tasks", "doctor_test_mime_type")
    op.drop_column("assessment_tasks", "doctor_test_original_name")
    op.drop_column("assessment_tasks", "doctor_test_path")
