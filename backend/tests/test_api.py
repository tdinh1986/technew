from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.orm import DigestReport, FetchJob


class TestReportsAPI:
    def test_latest_returns_404_when_empty(self, test_client: TestClient) -> None:
        resp = test_client.get("/api/reports/latest")
        assert resp.status_code == 404

    def test_latest_returns_digest_when_exists(
        self, test_client: TestClient, db_session: Session
    ) -> None:
        report = DigestReport(
            created_at=datetime.now(timezone.utc),
            article_count=5,
            topic_sections=[
                {
                    "topic": "AI",
                    "article_count": 5,
                    "actionable_insight": {"type": "Apply", "text": "Try it."},
                    "articles": [],
                }
            ],
        )
        db_session.add(report)
        db_session.commit()

        resp = test_client.get("/api/reports/latest")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["article_count"] == 5
        assert body["error"] is None
        assert len(body["data"]["topic_sections"]) == 1

    def test_list_returns_empty_array(self, test_client: TestClient) -> None:
        resp = test_client.get("/api/reports")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []
        assert body["meta"]["total"] == 0

    def test_response_matches_envelope_shape(self, test_client: TestClient) -> None:
        resp = test_client.get("/api/reports")
        body = resp.json()
        assert "data" in body
        assert "error" in body
        assert "meta" in body


class TestFetchAPI:
    def test_trigger_returns_202_with_job_id(self, test_client: TestClient) -> None:
        resp = test_client.post("/api/fetch")
        assert resp.status_code == 202
        body = resp.json()
        assert body["data"]["id"] is not None
        assert body["data"]["status"] == "queued"

    def test_get_job_returns_status(
        self, test_client: TestClient, db_session: Session
    ) -> None:
        job = FetchJob()
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        resp = test_client.get(f"/api/jobs/{job.id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "queued"

    def test_get_job_404_for_unknown_id(self, test_client: TestClient) -> None:
        resp = test_client.get("/api/jobs/nonexistent-id")
        assert resp.status_code == 404
