from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.orm import Article, DigestReport, Summary, TopicFilter

logger = logging.getLogger(__name__)


def assemble_digest_for_job(job_id: str, db: Session) -> DigestReport | None:
    """Assemble a digest scoped to articles created by a specific fetch job."""
    rows = (
        db.query(Summary, Article)
        .join(Article, Summary.article_id == Article.id)
        .filter(Article.summary_status == "summarized")
        .filter(Article.source_job_id == job_id)
        .all()
    )
    return _build_digest(rows, db)


def assemble_digest(db: Session) -> DigestReport | None:
    rows = (
        db.query(Summary, Article)
        .join(Article, Summary.article_id == Article.id)
        .filter(Article.summary_status == "summarized")
        .all()
    )
    return _build_digest(rows, db)


def _match_keyword(title: str, raw_content: str, keywords: list[str]) -> str | None:
    """Return the first keyword that appears (case-insensitive) in title or snippet."""
    haystack = (title + " " + raw_content[:500]).lower()
    for kw in keywords:
        if kw.lower() in haystack:
            return kw
    return None


def _build_digest(rows: list, db: Session) -> DigestReport | None:
    if not rows:
        logger.info("No summarized articles to assemble into digest")
        return None

    active_keywords = [
        tf.keyword
        for tf in db.query(TopicFilter).filter(TopicFilter.active.is_(True)).all()
    ]

    keyword_sections: dict[str, list[dict]] = defaultdict(list)
    fallback_sections: dict[str, list[dict]] = defaultdict(list)

    for summary, article in rows:
        matched = _match_keyword(article.title, article.raw_content, active_keywords)
        entry = {
            "id": article.id,
            "title": article.title,
            "source": article.source.type if article.source else "URL",
            "url": "",
            "bullets": summary.bullets,
            "_insights": summary.actionable_insights,
        }
        if matched:
            keyword_sections[matched].append(entry)
        else:
            llm_topic = summary.topic_tags[0] if summary.topic_tags else "General"
            fallback_sections[llm_topic].append(entry)

    def _sections_from(grouped: dict[str, list[dict]]) -> list[dict]:
        sections = []
        for topic, articles in grouped.items():
            best_insight = (
                articles[0]["_insights"][0]
                if articles[0]["_insights"]
                else {
                    "type": "Read More",
                    "text": "Explore these articles for more details.",
                }
            )
            clean_articles = [
                {k: v for k, v in a.items() if k != "_insights"} for a in articles
            ]
            sections.append(
                {
                    "topic": topic,
                    "article_count": len(articles),
                    "actionable_insight": best_insight,
                    "articles": clean_articles,
                }
            )
        return sections

    topic_sections = _sections_from(keyword_sections) + _sections_from(
        fallback_sections
    )
    total = sum(s["article_count"] for s in topic_sections)

    report = DigestReport(
        created_at=datetime.now(timezone.utc),
        article_count=total,
        topic_sections=topic_sections,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
