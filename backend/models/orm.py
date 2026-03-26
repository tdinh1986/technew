from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Enum,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(
        Enum("rss", "newsapi", "hackernews", name="source_type")
    )
    url: Mapped[str] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(default=True)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column()

    articles: Mapped[list[Article]] = relationship(back_populates="source")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sources.id")
    )
    fetched_at: Mapped[datetime] = mapped_column(default=_now)
    raw_content: Mapped[str] = mapped_column(Text, default="")
    summary_status: Mapped[str] = mapped_column(
        Enum("pending", "summarized", "pending-retry", name="summary_status"),
        default="pending",
    )

    source_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("fetch_jobs.id"), nullable=True
    )

    source: Mapped[Optional[Source]] = relationship(back_populates="articles")
    summary: Mapped[Optional[Summary]] = relationship(
        back_populates="article", uselist=False
    )


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id"), unique=True
    )
    bullets: Mapped[list[str]] = mapped_column(JSON)
    topic_tags: Mapped[list[str]] = mapped_column(JSON)
    actionable_insights: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    article: Mapped[Article] = relationship(back_populates="summary")


class DigestReport(Base):
    __tablename__ = "digest_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(default=_now, index=True)
    article_count: Mapped[int] = mapped_column()
    topic_sections: Mapped[list[dict[str, Any]]] = mapped_column(JSON)


class TopicFilter(Base):
    __tablename__ = "topic_filters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    keyword: Mapped[str] = mapped_column(Text, unique=True)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)


class FetchJob(Base):
    __tablename__ = "fetch_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    status: Mapped[str] = mapped_column(
        Enum("queued", "running", "done", "failed", name="job_status"),
        default="queued",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column()
    completed_at: Mapped[Optional[datetime]] = mapped_column()
    articles_added: Mapped[Optional[int]] = mapped_column()
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    report_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("digest_reports.id"), nullable=True
    )
