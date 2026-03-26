from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db
from config import Settings, get_settings
from digest import assemble_digest
from fetcher.deduplicator import deduplicate
from fetcher.hackernews import HNFetcher
from fetcher.newsapi import NewsAPIFetcher
from fetcher.rss import RSSFetcher
from models.orm import Article, FetchJob, Source
from models.schemas import ApiResponse, FetchJobOut
from summarizer.summarizer import batch_summarize

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_fetch_pipeline(job_id: str, settings: Settings) -> None:
    from db import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(FetchJob).filter(FetchJob.id == job_id).first()
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        sources = db.query(Source).filter(Source.enabled.is_(True)).all()
        rss_urls = [s.url for s in sources if s.type == "rss"]
        has_hn = any(s.type == "hackernews" for s in sources)
        newsapi_source = next((s for s in sources if s.type == "newsapi"), None)

        source_by_url: dict[str, str] = {s.url: s.id for s in sources if s.url}

        fetchers = []
        if rss_urls:
            fetchers.append(RSSFetcher(rss_urls))
        if has_hn:
            fetchers.append(HNFetcher())
        if newsapi_source and settings.news_api_key:
            fetchers.append(NewsAPIFetcher(settings.news_api_key))

        raw_articles = []
        for fetcher in fetchers:
            raw_articles.extend(await fetcher.fetch())

        new_articles = deduplicate(raw_articles, db)
        orm_articles = []
        for raw in new_articles:
            from fetcher.base import url_hash

            sid = source_by_url.get(raw.url)
            article = Article(
                url_hash=url_hash(raw.url),
                title=raw.title,
                raw_content=raw.snippet,
                fetched_at=datetime.now(timezone.utc),
                source_id=sid,
            )
            db.add(article)
            orm_articles.append(article)
        db.commit()
        for a in orm_articles:
            db.refresh(a)

        from summarizer.client import AnthropicLLMClient

        llm = AnthropicLLMClient(api_key=settings.anthropic_api_key)
        await batch_summarize(orm_articles, llm, db)
        assemble_digest(db)

        job.status = "done"
        job.completed_at = datetime.now(timezone.utc)
        job.articles_added = len(orm_articles)
        db.commit()
    except Exception as exc:
        logger.error("Fetch pipeline failed: %s", exc)
        job = db.query(FetchJob).filter(FetchJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@router.post("/fetch", status_code=202, response_model=ApiResponse[FetchJobOut])
def trigger_fetch(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    active = (
        db.query(FetchJob).filter(FetchJob.status.in_(["queued", "running"])).first()
    )
    if active:
        raise HTTPException(status_code=409, detail="A fetch is already in progress")

    job = FetchJob()
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(_run_fetch_pipeline, job.id, settings)
    return ApiResponse(data=FetchJobOut.model_validate(job))


@router.get("/jobs/{job_id}", response_model=ApiResponse[FetchJobOut])
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(FetchJob).filter(FetchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ApiResponse(data=FetchJobOut.model_validate(job))
