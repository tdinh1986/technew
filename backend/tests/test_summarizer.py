from __future__ import annotations

import json
import pytest
from sqlalchemy.orm import Session

from models.orm import Article, Summary
from summarizer.client import StubLLMClient
from summarizer.summarizer import batch_summarize


def _stub_response(article_ids: list[str]) -> str:
    return json.dumps(
        {
            "articles": [
                {
                    "id": aid,
                    "bullets": ["Point one.", "Point two.", "Point three."],
                    "topic": "Technology",
                    "actionable_insight": {"type": "Apply", "text": "Try it out."},
                }
                for aid in article_ids
            ]
        }
    )


@pytest.mark.asyncio
async def test_summaries_stored_for_pending_articles(
    db_session: Session, sample_articles: list[Article]
) -> None:
    ids = [a.id for a in sample_articles]
    llm = StubLLMClient(response=_stub_response(ids))
    await batch_summarize(sample_articles, llm, db_session)

    summaries = db_session.query(Summary).all()
    assert len(summaries) == 3
    for a in db_session.query(Article).all():
        assert a.summary_status == "summarized"


@pytest.mark.asyncio
async def test_already_summarized_articles_are_skipped(
    db_session: Session, sample_articles: list[Article]
) -> None:
    for a in sample_articles:
        a.summary_status = "summarized"
    db_session.commit()

    llm = StubLLMClient(response=_stub_response([]))
    await batch_summarize(sample_articles, llm, db_session)

    assert db_session.query(Summary).count() == 0


@pytest.mark.asyncio
async def test_pending_retry_set_on_llm_failure(
    db_session: Session, sample_articles: list[Article]
) -> None:
    class ErrorLLM(StubLLMClient):
        async def complete(self, messages, tools):
            raise RuntimeError("API down")

    await batch_summarize(sample_articles, ErrorLLM(response=""), db_session)

    for a in db_session.query(Article).all():
        assert a.summary_status == "pending-retry"
