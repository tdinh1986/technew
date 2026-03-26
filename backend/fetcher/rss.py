from __future__ import annotations

import logging
from datetime import datetime

import feedparser

from fetcher.base import AbstractFetcher, RawArticle

logger = logging.getLogger(__name__)


class RSSFetcher(AbstractFetcher):
    def __init__(self, feed_urls: list[str]) -> None:
        self._urls = feed_urls

    async def fetch(self) -> list[RawArticle]:
        articles: list[RawArticle] = []
        for url in self._urls:
            result = feedparser.parse(url)
            if result.bozo:
                logger.warning(
                    "Skipping malformed feed %s: %s", url, result.bozo_exception
                )
                continue
            for entry in result.entries:
                link = getattr(entry, "link", None)
                title = getattr(entry, "title", "")
                if not link or not title:
                    continue
                snippet = getattr(entry, "summary", "") or getattr(
                    entry, "description", ""
                )
                published = getattr(entry, "published_parsed", None)
                articles.append(
                    RawArticle(
                        url=link,
                        title=title,
                        snippet=snippet[:500],
                        source_name=result.feed.get("title", url),
                        published_at=datetime(*published[:6]) if published else None,
                    )
                )
        return articles
