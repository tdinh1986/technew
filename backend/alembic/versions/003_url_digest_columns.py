"""add source_job_id to articles and report_id to fetch_jobs

Revision ID: 003
Revises: 002
Create Date: 2026-03-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column(
            "source_job_id",
            sa.String(36),
            sa.ForeignKey("fetch_jobs.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "fetch_jobs",
        sa.Column(
            "report_id",
            sa.String(36),
            sa.ForeignKey("digest_reports.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("articles", "source_job_id")
    op.drop_column("fetch_jobs", "report_id")
