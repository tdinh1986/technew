from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.orm import Article, Summary
from summarizer.client import LLMClient
from summarizer.prompts import STORE_DIGEST_TOOL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def batch_summarize(articles: list[Article], llm: LLMClient, db: Session) -> None:
    pending = [a for a in articles if a.summary_status == "pending"]
    if not pending:
        return

    payload = [
        {"id": a.id, "title": a.title, "snippet": a.raw_content[:500]} for a in pending
    ]
    messages = [
        {
            "role": "user",
            "content": f"Summarize these articles:\n{json.dumps(payload)}",
        },
    ]

    try:
        raw = await llm.complete(
            messages=[
                {
                    "role": "user",
                    "content": json.dumps({"role": "system", "content": SYSTEM_PROMPT}),
                }
            ]
            + messages,
            tools=[STORE_DIGEST_TOOL],
        )
        result = json.loads(raw)
        summarized = {item["id"]: item for item in result.get("articles", [])}
    except Exception as exc:
        logger.error("LLM batch call failed: %s", exc)
        for a in pending:
            a.summary_status = "pending-retry"
        db.commit()
        return

    for article in pending:
        item = summarized.get(article.id)
        try:
            if not item or not item.get("bullets"):
                raise ValueError("missing or empty bullets")
            summary = Summary(
                article_id=article.id,
                bullets=item["bullets"],
                topic_tags=[item.get("topic", "General")],
                actionable_insights=[item["actionable_insight"]],
                created_at=datetime.now(timezone.utc),
            )
            db.add(summary)
            article.summary_status = "summarized"
        except Exception as exc:
            logger.warning(
                "Failed to store summary for %s: %s — storing fallback", article.id, exc
            )
            fallback = Summary(
                article_id=article.id,
                bullets=[article.raw_content[:200] or article.title],
                topic_tags=["General"],
                actionable_insights=[
                    {"type": "Read More", "text": "View the full article for details."}
                ],
                created_at=datetime.now(timezone.utc),
            )
            db.add(fallback)
            article.summary_status = "pending-retry"

    db.commit()
