from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fetcher.url_fetcher import URLFetcher, _parse


class TestParse:
    def test_extracts_title_and_snippet(self):
        html = """<html><head><title>Test Article</title></head>
        <body><p>This is a long enough paragraph with actual content that exceeds fifty characters.</p></body></html>"""
        result = _parse("https://example.com", html)
        assert result is not None
        assert result.title == "Test Article"
        assert "long enough paragraph" in result.snippet
        assert result.url == "https://example.com"
        assert result.source_name == "URL"

    def test_falls_back_to_og_title(self):
        html = """<html><head><meta property="og:title" content="OG Title"/></head>
        <body><p>Some paragraph content that is long enough to pass the fifty char filter.</p></body></html>"""
        result = _parse("https://example.com", html)
        assert result is not None
        assert result.title == "OG Title"

    def test_returns_none_when_no_title(self):
        html = "<html><head></head><body><p>No title here at all, even long paragraph.</p></body></html>"
        result = _parse("https://example.com", html)
        assert result is None

    def test_snippet_capped_at_500_chars(self):
        long_text = "A" * 1000
        html = f"<html><head><title>T</title></head><body><p>{long_text}</p></body></html>"
        result = _parse("https://example.com", html)
        assert result is not None
        assert len(result.snippet) <= 500

    def test_skips_short_paragraphs(self):
        html = """<html><head><title>Title</title></head>
        <body><p>Short.</p><p>This paragraph is long enough to pass the fifty character minimum filter check.</p></body></html>"""
        result = _parse("https://example.com", html)
        assert result is not None
        assert "long enough" in result.snippet


class TestURLFetcher:
    @pytest.mark.asyncio
    async def test_returns_articles_for_valid_urls(self):
        html = """<html><head><title>My Article</title></head>
        <body><p>This paragraph has more than fifty characters to pass the snippet filter.</p></body></html>"""

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = html

        with patch("fetcher.url_fetcher.httpx.AsyncClient") as mock_client_cls:
            instance = AsyncMock()
            instance.get = AsyncMock(return_value=mock_resp)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = instance

            fetcher = URLFetcher(["https://example.com/article"])
            results = await fetcher.fetch()

        assert len(results) == 1
        assert results[0].title == "My Article"
        assert results[0].url == "https://example.com/article"

    @pytest.mark.asyncio
    async def test_skips_failed_urls(self):
        import httpx

        with patch("fetcher.url_fetcher.httpx.AsyncClient") as mock_client_cls:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = instance

            fetcher = URLFetcher(["https://unreachable.example.com"])
            results = await fetcher.fetch()

        assert results == []

    @pytest.mark.asyncio
    async def test_partial_failure_continues(self):
        import httpx

        good_html = """<html><head><title>Good</title></head>
        <body><p>This is a paragraph that is definitely long enough to pass the fifty char check.</p></body></html>"""

        good_resp = MagicMock()
        good_resp.raise_for_status = MagicMock()
        good_resp.text = good_html

        call_count = 0

        async def side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.TimeoutException("timeout")
            return good_resp

        with patch("fetcher.url_fetcher.httpx.AsyncClient") as mock_client_cls:
            instance = AsyncMock()
            instance.get = side_effect
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = instance

            fetcher = URLFetcher(["https://bad.com", "https://good.com"])
            results = await fetcher.fetch()

        assert len(results) == 1
        assert results[0].title == "Good"
