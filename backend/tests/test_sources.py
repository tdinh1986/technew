from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from models.orm import Source


# ── Helpers ───────────────────────────────────────────────────────────────────


def _valid_feed():
    """Return a minimal feedparser result that passes validation."""
    import types

    feed = types.SimpleNamespace(
        bozo=False,
        bozo_exception=None,
        entries=[types.SimpleNamespace(title="Entry 1")],
        feed=types.SimpleNamespace(title="Test Feed"),
    )
    return feed


def _empty_feed():
    """Valid XML but no entries."""
    import types

    feed = types.SimpleNamespace(
        bozo=False,
        bozo_exception=None,
        entries=[],
        feed=types.SimpleNamespace(title="Empty Feed"),
    )
    return feed


def _bozo_feed():
    """Malformed XML."""
    import types

    feed = types.SimpleNamespace(
        bozo=True,
        bozo_exception=Exception("malformed XML"),
        entries=[],
        feed=types.SimpleNamespace(title=""),
    )
    return feed


# ── POST /api/sources ─────────────────────────────────────────────────────────


def test_create_source_valid_rss(test_client: TestClient, db_session):
    with patch("api.sources.feedparser.parse", return_value=_valid_feed()):
        resp = test_client.post(
            "/api/sources", json={"type": "rss", "url": "https://example.com/feed"}
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["type"] == "rss"
    assert data["url"] == "https://example.com/feed"
    assert data["enabled"] is True
    assert data["name"] == "Test Feed"
    # Row exists in DB
    row = db_session.query(Source).filter(Source.id == data["id"]).first()
    assert row is not None


def test_create_source_bozo_feed_rejected(test_client: TestClient):
    with patch("api.sources.feedparser.parse", return_value=_bozo_feed()):
        resp = test_client.post(
            "/api/sources", json={"type": "rss", "url": "https://bad-feed.example.com"}
        )
    assert resp.status_code == 422


def test_create_source_empty_feed_rejected(test_client: TestClient):
    with patch("api.sources.feedparser.parse", return_value=_empty_feed()):
        resp = test_client.post(
            "/api/sources", json={"type": "rss", "url": "https://empty-feed.example.com"}
        )
    assert resp.status_code == 422
    assert "no entries" in resp.json()["detail"].lower()


def test_create_hackernews_source_no_validation(test_client: TestClient):
    resp = test_client.post(
        "/api/sources", json={"type": "hackernews", "url": "https://news.ycombinator.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["type"] == "hackernews"


# ── GET /api/sources ──────────────────────────────────────────────────────────


def test_list_sources_includes_disabled(test_client: TestClient, db_session):
    db_session.add(Source(type="rss", url="https://a.com/feed", enabled=True))
    db_session.add(Source(type="rss", url="https://b.com/feed", enabled=False))
    db_session.commit()

    resp = test_client.get("/api/sources")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 2
    enabled_flags = {s["url"]: s["enabled"] for s in body["data"]}
    assert enabled_flags["https://a.com/feed"] is True
    assert enabled_flags["https://b.com/feed"] is False


# ── PATCH /api/sources/{id} ───────────────────────────────────────────────────


def test_disable_source_does_not_delete_row(test_client: TestClient, db_session):
    source = Source(type="rss", url="https://c.com/feed", enabled=True)
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    resp = test_client.patch(f"/api/sources/{source.id}", json={"enabled": False})
    assert resp.status_code == 200
    assert resp.json()["data"]["enabled"] is False

    # Row still exists
    row = db_session.query(Source).filter(Source.id == source.id).first()
    assert row is not None
    assert row.enabled is False


def test_patch_source_not_found(test_client: TestClient):
    resp = test_client.patch("/api/sources/nonexistent-id", json={"enabled": False})
    assert resp.status_code == 404


# ── DELETE /api/sources/{id} ──────────────────────────────────────────────────


def test_delete_source_soft_disables(test_client: TestClient, db_session):
    source = Source(type="hackernews", url="https://news.ycombinator.com", enabled=True)
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    resp = test_client.delete(f"/api/sources/{source.id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["enabled"] is False

    # Row still in DB (soft delete)
    row = db_session.query(Source).filter(Source.id == source.id).first()
    assert row is not None
    assert row.enabled is False
