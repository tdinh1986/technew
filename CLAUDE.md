# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TechNew** — a tech news aggregator and summarizer. The Python backend fetches articles from RSS feeds / news APIs, runs batch LLM summarization (via Anthropic SDK), and exposes a REST API. The Next.js frontend displays digest reports and lets the user trigger fetches manually.

## Architecture

```
technew/
├── backend/
│   ├── main.py           # FastAPI app entry; router registration; lifespan (scheduler start/stop)
│   ├── config.py         # Pydantic Settings; reads .env; rss_feeds property splits RSS_FEED_URLS
│   ├── db.py             # SQLAlchemy engine, SessionLocal, get_db(), init_db()
│   ├── digest.py         # assemble_digest(): groups articles by topic_tags[0], writes DigestReport JSON
│   ├── scheduler.py      # APScheduler IntervalTrigger; job ID "fetch_pipeline"
│   ├── api/
│   │   ├── fetch.py      # POST /fetch (202/409), GET /jobs/{id}; _run_fetch_pipeline as BackgroundTask
│   │   ├── reports.py    # GET /reports (last 30), GET /reports/latest
│   │   └── deps.py       # get_db, get_settings, get_llm_client
│   ├── fetcher/
│   │   ├── base.py       # AbstractFetcher ABC, RawArticle dataclass, url_hash() (SHA-256)
│   │   ├── rss.py        # RSSFetcher; skips bozo=True feeds; snippets capped at 500 chars
│   │   ├── newsapi.py    # NewsAPIFetcher; skipped silently if NEWS_API_KEY unset
│   │   ├── hackernews.py # HNFetcher; HN Algolia API; fallback to HN item URL for text posts
│   │   └── deduplicator.py  # Filters articles by url_hash vs DB; first-source-wins attribution
│   ├── models/
│   │   ├── orm.py        # Source, Article, Summary, DigestReport, FetchJob ORM models
│   │   └── schemas.py    # Pydantic v2 response models; ApiResponse[T] envelope
│   ├── summarizer/
│   │   ├── client.py     # LLMClient ABC; AnthropicLLMClient (claude-sonnet-4-6, 4096 tok); StubLLMClient
│   │   ├── prompts.py    # SYSTEM_PROMPT; store_digest tool-use JSON schema
│   │   └── summarizer.py # batch_summarize(): one LLM call/cycle; pending-retry on bad output
│   ├── tests/            # pytest; conftest.py fixtures; in-memory SQLite; StubLLMClient
│   └── alembic/          # DB migrations
└── frontend/
    ├── app/              # Next.js App Router pages (reports/page.tsx SSR + 60s ISR)
    ├── components/       # DigestReport, TopicSection, ArticleCard, FetchButton (SWR polling), EmptyState
    └── lib/              # api.ts (typed fetch helpers), types.ts (mirrors backend schemas)
```

### Key Patterns

- **`AbstractFetcher` ABC** — an exception in one fetcher returns an empty list; other sources continue unaffected. All fetchers are instantiated and run in `_run_fetch_pipeline` (`api/fetch.py`).
- **`LLMClient` ABC** — `AnthropicLLMClient` (prod, `claude-sonnet-4-6`, `max_tokens=4096`) vs `StubLLMClient` (tests). Injected via `get_llm_client()` in `api/deps.py`.
- **Batch summarization** — one LLM call per fetch cycle covers all pending articles. The `store_digest` tool-use schema in `summarizer/prompts.py` enforces structured output. Malformed output sets `summary_status = "pending-retry"`; no partial summary is persisted as authoritative.
- **Pre-computed digests** — `assemble_digest()` writes `DigestReport.topic_sections` as a JSON blob after each cycle. Reports are **not** assembled on read; the read path hits a single pre-computed row.
- **Job polling** — `POST /api/fetch` returns 202 immediately with `job_id`. The frontend polls `GET /api/jobs/{job_id}` via SWR every 3 seconds until status is `done` or `failed`.

---

## Backend

### Setup & Run
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Key Commands
```bash
pytest                              # run all tests
pytest tests/test_fetcher.py        # run single file
pytest -k "test_rss"               # run tests matching keyword
ruff check .                        # lint
ruff format .                       # format
```

### Environment Variables (`backend/.env`)
```
ANTHROPIC_API_KEY=...                          # required
RSS_FEED_URLS=https://...,https://...          # required; comma-separated RSS feed URLs
DATABASE_URL=sqlite:///./technew.db            # optional (default shown)
FETCH_INTERVAL_HOURS=6                         # optional (default shown)
NEWS_API_KEY=...                               # optional; enables NewsAPIFetcher
```

`RSS_FEED_URLS` is parsed by `config.py` via `settings.rss_feeds` (splits on `,`, strips whitespace).

---

## Frontend

### Setup & Run
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
npm run build && npm start
npm test             # vitest run (all component tests)
npm run lint
```

### Environment Variables (`frontend/.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Next.js rewrites `/api/*` to the backend via `next.config.ts`.

---

## Data Flow

1. **Trigger** — `POST /api/fetch` creates a `FetchJob` (status: `queued`) and enqueues `_run_fetch_pipeline` as a `BackgroundTask`; returns 202 with `job_id`.
2. **Fetch** — All fetchers (`RSSFetcher`, `HNFetcher`, optionally `NewsAPIFetcher`) run independently; failures return an empty list without blocking others.
3. **Deduplicate** — SHA-256 URL hash compared against `Article.url_hash` (UNIQUE index); only unseen articles proceed. First-source wins for attribution.
4. **Store** — New `Article` rows inserted with `summary_status = "pending"`.
5. **Summarize** — One LLM call for all pending articles using the `store_digest` tool-use schema. Non-conforming output → `summary_status = "pending-retry"`.
6. **Assemble** — `assemble_digest()` groups `summarized` articles by `topic_tags[0]`, serializes `topic_sections` as JSON, and writes a new `DigestReport` row.
7. **Serve** — `GET /api/reports/latest` reads the most recent pre-computed `DigestReport` row (< 200ms; no LLM on read path).
8. **Display** — Next.js SSR renders the digest; `FetchButton` polls job status every 3s via SWR and refreshes the digest on completion.

---

## API Endpoints

All routes prefixed with `/api`. Responses use the `ApiResponse[T]` envelope: `{ data, error, meta }`.

```
POST /api/fetch              → 202 {data: FetchJobOut}               | 409 if already running
GET  /api/jobs/{job_id}      → 200 {data: FetchJobOut}               | 404
GET  /api/reports            → 200 {data: DigestReportListItem[]}      (last 30, no topic sections)
GET  /api/reports/latest     → 200 {data: DigestReportOut}            | 404
```

`FetchJobOut` fields: `id`, `status` (`queued` | `running` | `done` | `failed`), `started_at`, `completed_at`, `articles_added`, `error_message`.

Frontend API calls live in `frontend/lib/api.ts`.

---

## Source Quality Rules

These rules govern which sources are acceptable and how quality is enforced end-to-end.

1. **Approved RSS sources** — Prefer established tech publications: Hacker News (`hnrss.org/frontpage`), Ars Technica, The Verge, Wired, MIT Technology Review, IEEE Spectrum. Avoid link aggregators, content farms, and sources without bylines.

2. **Validate feeds before configuring** — Before adding any URL to `RSS_FEED_URLS`, verify manually:
   - `feedparser.parse(url).bozo == False` (well-formed XML)
   - `len(feedparser.parse(url).entries) > 0` (non-empty feed)

   At runtime, `RSSFetcher` already skips `bozo=True` feeds with a warning log. This rule (FR-012) is a pre-configuration gate — a bad URL must not reach the env var.

3. **Article minimum requirements** — Every fetcher must drop articles missing either `url` or `title` (both are required, non-empty). This is enforced in all existing fetchers; new fetchers must match this behavior.

4. **Disable, never delete, sources** — Set `Source.enabled = False` to pause a misbehaving source. Deleting a `Source` row orphans its `Article` rows (FK reference). Soft-disable is the only sanctioned removal mechanism.

5. **Deduplication is global and final** — Dedup runs after all sources are merged, never before. Do not pre-filter by source. First URL wins attribution regardless of which source provided it.

6. **LLM output quality gate** — `batch_summarize()` accepts only tool-use responses where: `bullets` contains 3–5 items, `topic` is non-empty, and `actionable_insight` has both `type` (`Apply` | `Read More`) and `text`. Any deviation sets `summary_status = "pending-retry"`. Partial or degraded summaries are never surfaced as authoritative in the digest.

7. **Snippets only — no full HTML** — Fetchers must cap `raw_content` at 500 characters from the article's `summary`/`description` or API snippet field. Fetchers must not fetch full article HTML. This is enforced in `rss.py` and `hackernews.py` via `[:500]` slicing; all new fetchers must follow the same pattern.

---

## Key Dependencies

**Backend:** `fastapi`, `uvicorn`, `anthropic`, `feedparser`, `httpx`, `apscheduler`, `sqlalchemy`, `alembic`, `pydantic-settings`, `python-dotenv`

**Frontend:** Next.js 14 (App Router), Tailwind CSS, SWR
