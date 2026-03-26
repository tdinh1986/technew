from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import Settings

logger = logging.getLogger(__name__)


def _run_pipeline_sync(settings: Settings) -> None:
    from api.fetch import _run_fetch_pipeline

    asyncio.run(_run_fetch_pipeline("scheduled", settings))


def create_scheduler(settings: Settings) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_pipeline_sync,
        trigger=IntervalTrigger(hours=settings.fetch_interval_hours),
        args=[settings],
        id="fetch_pipeline",
        replace_existing=True,
    )
    return scheduler
