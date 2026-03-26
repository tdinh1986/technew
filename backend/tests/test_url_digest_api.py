from __future__ import annotations

import pytest


class TestUrlDigestEndpoint:
    def test_returns_202_with_job_id(self, test_client):
        resp = test_client.post(
            "/api/url-digest",
            json={"urls": ["https://example.com/article"]},
        )
        assert resp.status_code == 202
        data = resp.json()["data"]
        assert "id" in data
        assert data["status"] == "queued"
        assert data["report_id"] is None

    def test_rejects_empty_urls(self, test_client):
        resp = test_client.post("/api/url-digest", json={"urls": []})
        assert resp.status_code == 422

    def test_rejects_more_than_20_urls(self, test_client):
        urls = [f"https://example.com/article-{i}" for i in range(21)]
        resp = test_client.post("/api/url-digest", json={"urls": urls})
        assert resp.status_code == 422

    def test_rejects_malformed_url(self, test_client):
        resp = test_client.post(
            "/api/url-digest",
            json={"urls": ["not-a-url"]},
        )
        assert resp.status_code == 422

    def test_rejects_ftp_url(self, test_client):
        resp = test_client.post(
            "/api/url-digest",
            json={"urls": ["ftp://example.com/file"]},
        )
        assert resp.status_code == 422

    def test_accepts_exactly_20_urls(self, test_client):
        urls = [f"https://example.com/article-{i}" for i in range(20)]
        resp = test_client.post("/api/url-digest", json={"urls": urls})
        assert resp.status_code == 202


class TestGetReportById:
    def test_returns_404_for_unknown_id(self, test_client):
        resp = test_client.get("/api/reports/nonexistent-id")
        assert resp.status_code == 404

    def test_returns_report_when_exists(self, test_client, db_session):
        from datetime import datetime, timezone
        from models.orm import DigestReport

        report = DigestReport(
            article_count=1,
            topic_sections=[
                {
                    "topic": "Tech",
                    "article_count": 1,
                    "actionable_insight": {"type": "Read More", "text": "Read it."},
                    "articles": [
                        {
                            "id": "a1",
                            "title": "Test",
                            "source": "URL",
                            "url": "https://example.com",
                            "bullets": ["Point one"],
                        }
                    ],
                }
            ],
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)

        resp = test_client.get(f"/api/reports/{report.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == report.id
        assert data["article_count"] == 1
        assert len(data["topic_sections"]) == 1
