"""add knowledge base

Revision ID: 0004_knowledge_base
Revises: 0003_user_management
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0004_knowledge_base"
down_revision: str | None = "0003_user_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("attachment_path", sa.String(length=512), nullable=True),
        sa.Column("attachment_name", sa.String(length=255), nullable=True),
        sa.Column("attachment_mime_type", sa.String(length=128), nullable=True),
        sa.Column("attachment_size", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_entries_id"), "knowledge_entries", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_entries_title"), "knowledge_entries", ["title"], unique=False)
    op.create_index(op.f("ix_knowledge_entries_category"), "knowledge_entries", ["category"], unique=False)
    op.create_index(op.f("ix_knowledge_entries_created_by_id"), "knowledge_entries", ["created_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_entries_created_by_id"), table_name="knowledge_entries")
    op.drop_index(op.f("ix_knowledge_entries_category"), table_name="knowledge_entries")
    op.drop_index(op.f("ix_knowledge_entries_title"), table_name="knowledge_entries")
    op.drop_index(op.f("ix_knowledge_entries_id"), table_name="knowledge_entries")
    op.drop_table("knowledge_entries")
