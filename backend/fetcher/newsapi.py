from __future__ import annotations

import logging
from datetime import datetime

import httpx

from fetcher.base import AbstractFetcher, RawArticle

logger = logging.getLogger(__name__)

_ENDPOINT = "https://newsapi.org/v2/top-headlines"


class FetchSourceError(Exception):
    pass


class NewsAPIFetcher(AbstractFetcher):
    def __init__(self, api_key: str, category: str = "technology") -> None:
        self._api_key = api_key
        self._category = category

    async def fetch(self) -> list[RawArticle]:
        if not self._api_key:
            logger.info("NEWS_API_KEY not set — skipping NewsAPI source")
            return []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    _ENDPOINT,
                    params={
                        "apiKey": self._api_key,
                        "category": self._category,
                        "pageSize": 50,
                    },
                )
            if resp.status_code != 200:
                raise FetchSourceError(
                    f"NewsAPI returned {resp.status_code}: {resp.text[:200]}"
                )
            return [
                RawArticle(
                    url=a["url"],
                    title=a.get("title") or "",
                    snippet=(a.get("description") or "")[:500],
                    source_name=a.get("source", {}).get("name", "NewsAPI"),
                    published_at=_parse_dt(a.get("publishedAt")),
                )
                for a in resp.json().get("articles", [])
                if a.get("url") and a.get("title")
            ]
        except (httpx.HTTPError, httpx.TimeoutException, FetchSourceError) as exc:
            logger.error("NewsAPI fetch failed: %s", exc)
            return []


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
