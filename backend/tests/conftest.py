from __future__ import annotations

import json
import os
from collections.abc import Generator
from datetime import datetime, timezone

# Must come before any import that triggers get_settings() (e.g. db.py at module level)
os.environ.setdefault("ANTHROPIC_API_KEY", "test-placeholder")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from config import get_settings  # noqa: E402
from models.orm import Article, Base  # noqa: E402

# Clear lru_cache so the env var above is picked up on first call
get_settings.cache_clear()


# ── Database fixtures ──────────────────────────────────────────────────────────


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


# ── App / HTTP fixtures ────────────────────────────────────────────────────────


@pytest.fixture()
def test_client(db_session: Session) -> TestClient:
    from main import app
    from api.deps import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    # raise_server_exceptions=False suppresses background-task errors that use
    # their own DB session (not the test override); HTTP errors are unaffected.
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ── LLM stub ──────────────────────────────────────────────────────────────────

STUB_LLM_RESPONSE = json.dumps(
    {
        "articles": [
            {
                "id": "placeholder",
                "bullets": [
                    "Key point one about this article.",
                    "Key point two about this article.",
                    "Key point three about this article.",
                ],
                "topic": "Technology",
                "actionable_insight": {
                    "type": "Read More",
                    "text": "Explore the full article for implementation details.",
                },
            }
        ]
    }
)


@pytest.fixture()
def stub_llm_client():
    from summarizer.client import StubLLMClient

    return StubLLMClient(response=STUB_LLM_RESPONSE)


# ── Sample data fixtures ───────────────────────────────────────────────────────


@pytest.fixture()
def sample_articles(db_session: Session) -> list[Article]:
    articles = [
        Article(
            id=f"article-{i}",
            url_hash=f"hash{i:064d}",
            title=f"Test Article {i}",
            raw_content=f"Content of test article {i}.",
            fetched_at=datetime.now(timezone.utc),
            summary_status="pending",
        )
        for i in range(1, 4)
    ]
    db_session.add_all(articles)
    db_session.commit()
    return articles
