from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from api.deps import get_db
from config import Settings, get_settings
from digest import assemble_digest_for_job
from fetcher.base import url_hash
from fetcher.deduplicator import deduplicate
from fetcher.url_fetcher import URLFetcher
from models.orm import Article, FetchJob
from models.schemas import ApiResponse, FetchJobOut, UrlDigestRequest
from summarizer.summarizer import batch_summarize

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_url_pipeline(job_id: str, urls: list[str], settings: Settings) -> None:
    from db import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(FetchJob).filter(FetchJob.id == job_id).first()
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        raw_articles = await URLFetcher(urls).fetch()
        new_articles = deduplicate(raw_articles, db)

        orm_articles = []
        for raw in new_articles:
            article = Article(
                url_hash=url_hash(raw.url),
                title=raw.title,
                raw_content=raw.snippet,
                fetched_at=datetime.now(timezone.utc),
                source_job_id=job_id,
            )
            db.add(article)
            orm_articles.append(article)
        db.commit()
        for a in orm_articles:
            db.refresh(a)

        from summarizer.client import AnthropicLLMClient

        llm = AnthropicLLMClient(api_key=settings.anthropic_api_key)
        await batch_summarize(orm_articles, llm, db)

        report = assemble_digest_for_job(job_id, db)

        job.status = "done"
        job.completed_at = datetime.now(timezone.utc)
        job.articles_added = len(orm_articles)
        job.report_id = report.id if report else None
        db.commit()
    except Exception as exc:
        logger.error("URL digest pipeline failed: %s", exc)
        job = db.query(FetchJob).filter(FetchJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@router.post("/url-digest", status_code=202, response_model=ApiResponse[FetchJobOut])
def submit_url_digest(
    body: UrlDigestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    job = FetchJob()
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(_run_url_pipeline, job.id, body.urls, settings)
    return ApiResponse(data=FetchJobOut.model_validate(job))
