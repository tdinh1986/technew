"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "type",
            sa.Enum("rss", "newsapi", "hackernews", name="source_type"),
            nullable=False,
        ),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("last_fetched_at", sa.DateTime, nullable=True),
    )
    op.create_table(
        "articles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("url_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column(
            "source_id", sa.String(36), sa.ForeignKey("sources.id"), nullable=True
        ),
        sa.Column("fetched_at", sa.DateTime, nullable=False),
        sa.Column("raw_content", sa.Text, nullable=False, default=""),
        sa.Column(
            "summary_status",
            sa.Enum("pending", "summarized", "pending-retry", name="summary_status"),
            nullable=False,
            default="pending",
        ),
    )
    op.create_index("ix_articles_url_hash", "articles", ["url_hash"])
    op.create_table(
        "summaries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "article_id",
            sa.String(36),
            sa.ForeignKey("articles.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("bullets", sa.JSON, nullable=False),
        sa.Column("topic_tags", sa.JSON, nullable=False),
        sa.Column("actionable_insights", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "digest_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("article_count", sa.Integer, nullable=False),
        sa.Column("topic_sections", sa.JSON, nullable=False),
    )
    op.create_index("ix_digest_reports_created_at", "digest_reports", ["created_at"])
    op.create_table(
        "fetch_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "done", "failed", name="job_status"),
            nullable=False,
            default="queued",
        ),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("articles_added", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("fetch_jobs")
    op.drop_index("ix_digest_reports_created_at", "digest_reports")
    op.drop_table("digest_reports")
    op.drop_table("summaries")
    op.drop_index("ix_articles_url_hash", "articles")
    op.drop_table("articles")
    op.drop_table("sources")
