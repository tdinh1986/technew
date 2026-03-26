from __future__ import annotations

import logging

import httpx
from bs4 import BeautifulSoup

from fetcher.base import AbstractFetcher, RawArticle

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TechNew/1.0; +https://github.com/technew)"
}


class URLFetcher(AbstractFetcher):
    def __init__(self, urls: list[str]) -> None:
        self._urls = urls

    async def fetch(self) -> list[RawArticle]:
        results: list[RawArticle] = []
        async with httpx.AsyncClient(
            timeout=10, headers=_HEADERS, follow_redirects=True
        ) as client:
            for url in self._urls:
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    article = _parse(url, resp.text)
                    if article:
                        results.append(article)
                except (httpx.HTTPError, httpx.TimeoutException) as exc:
                    logger.warning("URL fetch failed for %s: %s", url, exc)
        return results


def _parse(url: str, html: str) -> RawArticle | None:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = og["content"].strip()

    if not title:
        logger.debug("No title found for %s — skipping", url)
        return None

    # Extract visible text from paragraphs / article body
    snippet = ""
    for tag in soup.find_all(["p", "article"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 50:  # skip tiny fragments
            snippet = text[:500]
            break

    return RawArticle(
        url=url,
        title=title,
        snippet=snippet,
        source_name="URL",
    )
