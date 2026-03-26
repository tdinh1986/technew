from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.fetch import router as fetch_router
from api.reports import router as reports_router
from api.sources import router as sources_router
from api.summarize import router as summarize_router
from api.topics import router as topics_router
from config import get_settings
from db import SessionLocal, init_db
from scheduler import create_scheduler

logger = logging.getLogger(__name__)


def _seed_sources_from_config() -> None:
    """On first startup, populate Source rows from env config if table is empty."""
    from models.orm import Source

    settings = get_settings()
    db = SessionLocal()
    try:
        if db.query(Source).count() > 0:
            return
        for url in settings.rss_feeds:
            url = url.strip()
            if url:
                db.add(Source(type="rss", url=url))
        db.add(Source(type="hackernews", url="https://news.ycombinator.com"))
        if settings.news_api_key:
            db.add(Source(type="newsapi", url="https://newsapi.org"))
        db.commit()
        logger.info("Seeded initial sources from config")
    except Exception as exc:
        logger.warning("Could not seed sources: %s", exc)
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _seed_sources_from_config()
    scheduler = create_scheduler(get_settings())
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="TechNew API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fetch_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(summarize_router, prefix="/api")
app.include_router(topics_router, prefix="/api")
