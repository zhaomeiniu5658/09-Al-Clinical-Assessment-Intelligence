"""add xfyun asr settings

Revision ID: 0002_xfyun_asr_settings
Revises: 0001_initial
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_xfyun_asr_settings"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "xfyun_asr_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("app_id", sa.String(length=255), nullable=False),
        sa.Column("api_secret", sa.String(length=512), nullable=False),
        sa.Column("api_key", sa.String(length=512), nullable=False),
        sa.Column("web_api", sa.String(length=512), nullable=False),
        sa.Column("hotwords", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("xfyun_asr_settings")
