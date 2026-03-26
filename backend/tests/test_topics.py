from __future__ import annotations

from fastapi.testclient import TestClient

from models.orm import TopicFilter


# ── POST /api/topics ──────────────────────────────────────────────────────────


def test_create_topic(test_client: TestClient, db_session):
    resp = test_client.post("/api/topics", json={"keyword": "AI"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["keyword"] == "AI"
    assert data["active"] is True
    assert "id" in data
    assert "created_at" in data

    row = db_session.query(TopicFilter).filter(TopicFilter.keyword == "AI").first()
    assert row is not None


def test_create_duplicate_topic_returns_409(test_client: TestClient):
    test_client.post("/api/topics", json={"keyword": "Security"})
    resp = test_client.post("/api/topics", json={"keyword": "Security"})
    assert resp.status_code == 409


# ── GET /api/topics ───────────────────────────────────────────────────────────


def test_list_topics(test_client: TestClient, db_session):
    db_session.add(TopicFilter(keyword="Rust"))
    db_session.add(TopicFilter(keyword="Python"))
    db_session.commit()

    resp = test_client.get("/api/topics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 2
    keywords = {t["keyword"] for t in body["data"]}
    assert keywords == {"Rust", "Python"}


def test_list_topics_empty(test_client: TestClient):
    resp = test_client.get("/api/topics")
    assert resp.status_code == 200
    assert resp.json()["data"] == []
    assert resp.json()["meta"]["total"] == 0


# ── DELETE /api/topics/{id} ───────────────────────────────────────────────────


def test_delete_topic_hard_deletes_row(test_client: TestClient, db_session):
    topic = TopicFilter(keyword="Cloud")
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    resp = test_client.delete(f"/api/topics/{topic.id}")
    assert resp.status_code == 200

    row = db_session.query(TopicFilter).filter(TopicFilter.id == topic.id).first()
    assert row is None


def test_delete_topic_not_found(test_client: TestClient):
    resp = test_client.delete("/api/topics/nonexistent-id")
    assert resp.status_code == 404
