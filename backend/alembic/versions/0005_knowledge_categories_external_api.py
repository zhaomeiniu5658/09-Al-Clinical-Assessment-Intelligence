"""add knowledge categories and external API settings

Revision ID: 0005_knowledge_ext_api
Revises: 0004_knowledge_base
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005_knowledge_ext_api"
down_revision: str | None = "0004_knowledge_base"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("knowledge_categories"):
        op.create_table(
            "knowledge_categories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        op.create_index(op.f("ix_knowledge_categories_id"), "knowledge_categories", ["id"], unique=False)
    if not inspector.has_table("knowledge_external_api_settings"):
        op.create_table(
            "knowledge_external_api_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("api_key_hash", sa.String(length=64), nullable=False, server_default=""),
            sa.Column("api_key_prefix", sa.String(length=24), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    op.drop_table("knowledge_external_api_settings")
    op.drop_index(op.f("ix_knowledge_categories_id"), table_name="knowledge_categories")
    op.drop_table("knowledge_categories")
