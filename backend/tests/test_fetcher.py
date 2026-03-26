from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from fetcher.base import RawArticle, url_hash
from fetcher.deduplicator import deduplicate
from models.orm import Article
from datetime import datetime, timezone


def _make_raw(n: int) -> RawArticle:
    return RawArticle(
        url=f"https://example.com/article/{n}",
        title=f"Article {n}",
        snippet=f"Snippet {n}",
        source_name="Test Source",
        published_at=datetime.now(timezone.utc),
    )


# ── Deduplicator ──────────────────────────────────────────────────────────────


class TestDeduplicate:
    def test_returns_all_when_db_empty(self, db_session: Session) -> None:
        articles = [_make_raw(1), _make_raw(2)]
        result = deduplicate(articles, db_session)
        assert len(result) == 2

    def test_filters_existing_hashes(self, db_session: Session) -> None:
        raw = _make_raw(1)
        existing = Article(
            id="existing-1",
            url_hash=url_hash(raw.url),
            title=raw.title,
            raw_content=raw.snippet,
            fetched_at=datetime.now(timezone.utc),
        )
        db_session.add(existing)
        db_session.commit()

        result = deduplicate([raw, _make_raw(2)], db_session)
        assert len(result) == 1
        assert result[0].url == "https://example.com/article/2"

    def test_idempotent_second_run(self, db_session: Session) -> None:
        articles = [_make_raw(1), _make_raw(2)]
        first = deduplicate(articles, db_session)
        # Simulate persisting them
        for a in first:
            db_session.add(
                Article(
                    id=f"id-{url_hash(a.url)[:8]}",
                    url_hash=url_hash(a.url),
                    title=a.title,
                    raw_content=a.snippet,
                    fetched_at=datetime.now(timezone.utc),
                )
            )
        db_session.commit()
        second = deduplicate(articles, db_session)
        assert second == []

    def test_empty_input(self, db_session: Session) -> None:
        assert deduplicate([], db_session) == []


# ── RSS Fetcher ───────────────────────────────────────────────────────────────


class TestRSSFetcher:
    @pytest.mark.asyncio
    async def test_returns_articles_from_valid_feed(self) -> None:
        from fetcher.rss import RSSFetcher

        mock_result = type(
            "R",
            (),
            {
                "bozo": False,
                "bozo_exception": None,
                "feed": {"title": "Tech Feed"},
                "entries": [
                    type(
                        "E",
                        (),
                        {
                            "link": "https://example.com/1",
                            "title": "Entry 1",
                            "summary": "Summary 1",
                            "published_parsed": (2026, 3, 24, 12, 0, 0, 0, 0, 0),
                        },
                    )(),
                ],
            },
        )()
        with patch("feedparser.parse", return_value=mock_result):
            fetcher = RSSFetcher(["https://example.com/feed"])
            articles = await fetcher.fetch()
        assert len(articles) == 1
        assert articles[0].title == "Entry 1"

    @pytest.mark.asyncio
    async def test_skips_bozo_feed(self) -> None:
        from fetcher.rss import RSSFetcher

        mock_result = type(
            "R",
            (),
            {
                "bozo": True,
                "bozo_exception": Exception("bad xml"),
                "entries": [],
            },
        )()
        with patch("feedparser.parse", return_value=mock_result):
            fetcher = RSSFetcher(["https://bad-feed.com/rss"])
            articles = await fetcher.fetch()
        assert articles == []


# ── NewsAPI Fetcher ───────────────────────────────────────────────────────────


class TestNewsAPIFetcher:
    @pytest.mark.asyncio
    async def test_skips_when_no_api_key(self) -> None:
        from fetcher.newsapi import NewsAPIFetcher

        fetcher = NewsAPIFetcher(api_key="")
        articles = await fetcher.fetch()
        assert articles == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_http_error(self) -> None:
        import httpx
        from fetcher.newsapi import NewsAPIFetcher

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                side_effect=httpx.ConnectError("timeout")
            )
            fetcher = NewsAPIFetcher(api_key="test-key")
            articles = await fetcher.fetch()
        assert articles == []


# ── HN Fetcher ────────────────────────────────────────────────────────────────


class TestHNFetcher:
    @pytest.mark.asyncio
    async def test_returns_empty_on_network_error(self) -> None:
        import httpx
        from fetcher.hackernews import HNFetcher

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                side_effect=httpx.ConnectError("timeout")
            )
            fetcher = HNFetcher()
            articles = await fetcher.fetch()
        assert articles == []

    @pytest.mark.asyncio
    async def test_uses_hn_url_when_story_has_no_url(self) -> None:
        from fetcher.hackernews import HNFetcher

        mock_resp = MagicMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = {
            "hits": [
                {
                    "objectID": "12345",
                    "title": "Ask HN: something",
                    "url": None,
                    "story_text": "text",
                }
            ]
        }
        with patch("httpx.AsyncClient") as mock_client:
            instance = AsyncMock()
            instance.get = AsyncMock(return_value=mock_resp)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            fetcher = HNFetcher()
            articles = await fetcher.fetch()
        assert len(articles) == 1
        assert "news.ycombinator.com/item?id=12345" in articles[0].url
