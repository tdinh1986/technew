"""add topic_filters and source name

Revision ID: 002
Revises: 001
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("name", sa.Text, nullable=True))
    op.create_table(
        "topic_filters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("keyword", sa.Text, nullable=False, unique=True),
        sa.Column("active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("topic_filters")
    op.drop_column("sources", "name")
