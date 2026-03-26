from __future__ import annotations

import logging

import httpx

from fetcher.base import AbstractFetcher, RawArticle

logger = logging.getLogger(__name__)

_ENDPOINT = "https://hn.algolia.com/api/v1/search"


class HNFetcher(AbstractFetcher):
    def __init__(self, hits_per_page: int = 30) -> None:
        self._hits_per_page = hits_per_page

    async def fetch(self) -> list[RawArticle]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    _ENDPOINT,
                    params={"tags": "front_page", "hitsPerPage": self._hits_per_page},
                )
            resp.raise_for_status()
            return [
                RawArticle(
                    url=hit.get("url")
                    or f"https://news.ycombinator.com/item?id={hit['objectID']}",
                    title=hit.get("title") or hit.get("story_title") or "",
                    snippet=(hit.get("story_text") or "")[:500],
                    source_name="Hacker News",
                )
                for hit in resp.json().get("hits", [])
                if hit.get("title") or hit.get("story_title")
            ]
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.error("Hacker News fetch failed: %s", exc)
            return []
