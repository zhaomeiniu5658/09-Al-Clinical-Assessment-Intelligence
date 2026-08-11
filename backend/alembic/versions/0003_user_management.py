"""add user management fields

Revision ID: 0003_user_management
Revises: 0002_xfyun_asr_settings
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0003_user_management"
down_revision: str | None = "0002_xfyun_asr_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    op.drop_column("users", "is_admin")
