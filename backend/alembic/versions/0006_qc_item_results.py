"""add qc item results

Revision ID: 0006_qc_item_results
Revises: 0005_knowledge_ext_api
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0006_qc_item_results"
down_revision: str | None = "0005_knowledge_ext_api"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("qc_results", sa.Column("item_results", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("qc_results", "item_results")
