from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from digest import assemble_digest
from models.orm import Article, Summary, TopicFilter


def _seed_summarized(db: Session, n: int = 3) -> list[Article]:
    articles = []
    for i in range(n):
        a = Article(
            id=f"art-{i}",
            url_hash=f"{'0' * 60}{i:04d}",
            title=f"Article {i}",
            raw_content=f"Content {i}",
            fetched_at=datetime.now(timezone.utc),
            summary_status="summarized",
        )
        db.add(a)
        db.flush()
        s = Summary(
            article_id=a.id,
            bullets=["Bullet 1.", "Bullet 2.", "Bullet 3."],
            topic_tags=["Technology"],
            actionable_insights=[{"type": "Apply", "text": "Do something."}],
            created_at=datetime.now(timezone.utc),
        )
        db.add(s)
        articles.append(a)
    db.commit()
    return articles


def test_assemble_digest_groups_by_topic(db_session: Session) -> None:
    _seed_summarized(db_session, 3)
    report = assemble_digest(db_session)
    assert report is not None
    assert report.article_count == 3
    assert len(report.topic_sections) == 1
    assert report.topic_sections[0]["topic"] == "Technology"


def test_assemble_digest_returns_none_when_no_summaries(db_session: Session) -> None:
    result = assemble_digest(db_session)
    assert result is None


def test_digest_has_actionable_insight_per_section(db_session: Session) -> None:
    _seed_summarized(db_session, 2)
    report = assemble_digest(db_session)
    for section in report.topic_sections:
        assert "actionable_insight" in section
        assert section["actionable_insight"]["type"] in ("Apply", "Read More")


# ── Topic keyword matching tests ──────────────────────────────────────────────


def _seed_article_with_title(db: Session, title: str, topic_tag: str, article_id: str) -> Article:
    a = Article(
        id=article_id,
        url_hash=f"{'0' * 56}{article_id[-8:]}",
        title=title,
        raw_content=f"Content about {title}.",
        fetched_at=datetime.now(timezone.utc),
        summary_status="summarized",
    )
    db.add(a)
    db.flush()
    s = Summary(
        article_id=a.id,
        bullets=["Bullet 1.", "Bullet 2.", "Bullet 3."],
        topic_tags=[topic_tag],
        actionable_insights=[{"type": "Apply", "text": "Do something."}],
        created_at=datetime.now(timezone.utc),
    )
    db.add(s)
    db.commit()
    return a


def test_keyword_match_overrides_llm_topic(db_session: Session) -> None:
    """Article whose title matches a TopicFilter keyword appears in keyword section."""
    _seed_article_with_title(db_session, "New AI breakthrough announced", "Technology", "kw-art-1")
    db_session.add(TopicFilter(keyword="AI", active=True))
    db_session.commit()

    report = assemble_digest(db_session)
    assert report is not None
    section_topics = [s["topic"] for s in report.topic_sections]
    assert "AI" in section_topics
    ai_section = next(s for s in report.topic_sections if s["topic"] == "AI")
    assert ai_section["article_count"] == 1
    assert ai_section["articles"][0]["title"] == "New AI breakthrough announced"


def test_no_keyword_match_falls_back_to_llm_topic(db_session: Session) -> None:
    """Article with no matching keyword retains its LLM-assigned topic."""
    _seed_article_with_title(db_session, "Python 4.0 released", "Programming", "fb-art-1")
    db_session.add(TopicFilter(keyword="Security", active=True))
    db_session.commit()

    report = assemble_digest(db_session)
    assert report is not None
    section_topics = [s["topic"] for s in report.topic_sections]
    assert "Programming" in section_topics
    assert "Security" not in section_topics


def test_keyword_sections_appear_before_fallback_sections(db_session: Session) -> None:
    """Keyword-matched sections come before LLM-grouped fallback sections."""
    _seed_article_with_title(db_session, "Rust memory safety deep dive", "Systems", "ord-art-1")
    _seed_article_with_title(db_session, "General cloud computing news", "Cloud", "ord-art-2")
    db_session.add(TopicFilter(keyword="Rust", active=True))
    db_session.commit()

    report = assemble_digest(db_session)
    topics_in_order = [s["topic"] for s in report.topic_sections]
    rust_idx = topics_in_order.index("Rust")
    cloud_idx = topics_in_order.index("Cloud")
    assert rust_idx < cloud_idx
