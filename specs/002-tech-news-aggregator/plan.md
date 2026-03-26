# Implementation Plan: Tech News Aggregator & Digest (P1 Features)

**Branch**: `002-tech-news-aggregator` | **Date**: 2026-03-24 | **Spec**: `specs/002-tech-news-aggregator/spec.md`

**Scope**: P1 user stories only — Daily Digest Report, Multi-Source News Fetching, AI Summarization with Actionable Insights (FR-001–FR-007, FR-010–FR-011, FR-013–FR-014).

---

## Summary

Build the MVP core of TechNew: a Python/FastAPI backend that fetches articles from RSS feeds, NewsAPI, and Hacker News on a schedule, summarizes them in batch via Claude AI into a structured digest with actionable insights, and persists the result for fast SSR delivery by a Next.js frontend. The read path never touches the LLM — all AI work is pre-computed and stored.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), Node.js 20 / Next.js 14 (frontend)
**Primary Dependencies**: FastAPI, APScheduler, feedparser, httpx, anthropic-sdk, SQLAlchemy, Pydantic v2, Alembic | Next.js App Router, Tailwind CSS, SWR
**Storage**: SQLite (development) via SQLAlchemy ORM + Alembic migrations; swappable to PostgreSQL via `DATABASE_URL`
**Testing**: pytest + httpx (backend integration, real SQLite); vitest + @testing-library/react (frontend)
**Target Platform**: Local machine / single-user server (Linux/macOS)
**Project Type**: Web application (Python API + Next.js frontend)
**Performance Goals**: Report endpoint < 200ms; manual fetch response < 100ms (async job); frontend SSR < 2s
**Constraints**: Single-user; no auth required for P1; LLM on write path only (never on read); no concurrent fetch for the same source
**Scale/Scope**: ~5–20 news sources; ~50–200 articles per fetch cycle; daily digest report

---

## Constitution Check

| Principle | Gate | Status | Notes |
|-----------|------|--------|-------|
| P1 — Single Responsibility Per Module | Each file owns exactly one concern | ✓ PASS | fetcher / summarizer / scheduler / db are separate modules |
| P2 — Pydantic-First Data Contracts | All inter-layer data validated by Pydantic models | ✓ PASS | DB models (SQLAlchemy) separate from API models (Pydantic) |
| P3 — Idempotent Fetch Operations | URL-hash dedup enforced before insert | ✓ PASS | `articles.url_hash` has a UNIQUE constraint; upsert-or-skip on conflict |
| P4 — BDD Integration Tests | Tests hit real SQLite in-memory; no DB mocks | ✓ PASS | pytest fixture spins up in-memory SQLite; httpx TestClient used |
| P5 — LLM Call Isolation | `LLMClient` protocol injected at startup | ✓ PASS | `summarizer.py` depends on `LLMClient` ABC; `StubLLMClient` for tests |
| P6 — Report-First IA | `/` routes to digest view; no article-list landing page | ✓ PASS | Next.js root page renders `DigestReport`; `/articles` not in P1 |
| P7 — Readable Typography | Max-width prose container; Tailwind only | ✓ PASS | `prose max-w-2xl` wrapper; no custom CSS files |
| P8 — API Response Budget | Report list < 200ms; fetch trigger async | ✓ PASS | Read path: DB query only. Trigger: enqueue + return job_id immediately |
| P9 — Background Processing | APScheduler runs fetch+summarize out-of-band | ✓ PASS | `BackgroundScheduler` starts on FastAPI lifespan; HTTP never blocks |
| P10 — Secrets Via Env Only | All keys from `.env` via python-dotenv | ✓ PASS | `config.py` uses `pydantic-settings`; `.env` in `.gitignore` |
| P11 — No User-Controlled Shell Execution | No subprocess calls; URLs stored as data | ✓ PASS | feedparser and httpx consume URLs as strings only |

---

## Architecture Decisions

### ADR-1: Job Queue — APScheduler in-process vs External Queue (Celery/RQ)

| | APScheduler | Celery + Redis |
|---|---|---|
| Complexity | Low — single process, no broker | High — requires Redis, worker process, broker config |
| Ops overhead | None | Redis + worker daemon |
| Fit for scope | Single-user, ~5 fetch cycles/day | Multi-tenant, high-throughput |

**Choice**: APScheduler `BackgroundScheduler` running inside the FastAPI process.
**Rationale**: Single-user scope (constitution) doesn't justify broker infrastructure. APScheduler satisfies P9 (background processing) without additional services. Swappable later. (P1, P9)

---

### ADR-2: Database — SQLite vs PostgreSQL

**Choice**: SQLite via SQLAlchemy ORM, with `DATABASE_URL` env var for swap-to-Postgres.
**Rationale**: Single-user, local-first app. SQLite needs zero infrastructure. ORM + Alembic migrations make the swap to Postgres a one-line env change when needed. (P10, P8)

---

### ADR-3: LLM Summarization Strategy — Per-Article vs Batch

| | Per-Article | Batch (one call per fetch cycle) |
|---|---|---|
| LLM cost | High (N calls) | Low (1–2 calls per cycle) |
| Prompt control | Simple | Structured JSON output required |
| Partial failure | Easy to retry one | Must handle partial JSON |

**Choice**: Batch per fetch cycle — one LLM call with all new article titles + snippets, requesting structured JSON output with per-article bullets + topic grouping + actionable insights in a single response.
**Rationale**: Dramatically reduces API cost and latency. Structured JSON output from Claude is reliable with `claude-sonnet-4-6`. Partial failure handled by marking individual article summaries as `pending-retry` from the parsed response. (P5, P9, P11)

---

### ADR-4: Topic Matching — LLM-Based vs Keyword-Based

**Choice**: Keyword-based matching at article-ingest time (title + snippet substring/regex match against `TopicFilter.keyword`).
**Rationale**: Deterministic, zero LLM cost, instant. Sufficient for P1 where topics are user-defined keywords (e.g., "AI", "Rust", "LLM"). LLM-semantic matching is a P2+ enhancement. (P3, P8)

---

### ADR-5: Frontend Data Fetching — SWR Polling vs WebSocket vs SSE

**Choice**: SWR with polling on the job-status endpoint (`GET /api/jobs/{job_id}`) at 3-second intervals while job is active; switches to static once `done`.
**Rationale**: WebSockets and SSE add server complexity. For P1, manual fetch is infrequent and a 3-second polling window well within the 60-second SC-003 target. (P8, P9)

---

### ADR-6: DigestReport Assembly — Pre-Computed vs On-Read

**Choice**: DigestReport is assembled and stored immediately after the summarization job completes. The read endpoint returns stored JSON.
**Rationale**: Direct compliance with P8 (< 200ms report endpoint) and FR-014. No computation on the read path. (P6, P8)

---

## Project Structure

### Documentation (this feature)

```text
specs/002-tech-news-aggregator/
├── spec.md
├── plan.md              ← this file
└── tasks.md             ← created by /speckit.tasks
```

### Source Code

```text
backend/
├── main.py                  # FastAPI app, lifespan (scheduler start/stop)
├── config.py                # pydantic-settings: loads .env, exposes Settings singleton
├── db.py                    # SQLAlchemy engine, session factory, Base
├── models/
│   ├── orm.py               # SQLAlchemy ORM table definitions (Article, Summary, DigestReport, Source, FetchJob)
│   └── schemas.py           # Pydantic v2 request/response models (separate from ORM)
├── fetcher/
│   ├── __init__.py
│   ├── base.py              # AbstractFetcher protocol
│   ├── rss.py               # feedparser-based RSS fetcher
│   ├── newsapi.py           # httpx-based NewsAPI fetcher
│   └── hackernews.py        # httpx-based HN Algolia API fetcher
├── summarizer/
│   ├── __init__.py
│   ├── client.py            # LLMClient ABC + AnthropicLLMClient + StubLLMClient
│   ├── prompts.py           # Prompt templates (batch summarize + insight extraction)
│   └── summarizer.py        # Orchestrates batch call → parse → store summaries + digest
├── scheduler.py             # APScheduler setup; registers fetch+summarize job
├── digest.py                # DigestReport assembly from stored summaries
├── api/
│   ├── reports.py           # GET /api/reports, GET /api/reports/latest
│   ├── fetch.py             # POST /api/fetch (enqueue), GET /api/jobs/{job_id}
│   └── deps.py              # FastAPI dependency injection (db session, llm_client)
├── alembic/                 # DB migrations
│   └── versions/
├── tests/
│   ├── conftest.py          # pytest fixtures: in-memory SQLite, StubLLMClient, TestClient
│   ├── test_fetcher.py      # Integration: fetcher → DB state (fixture feed data)
│   ├── test_summarizer.py   # Integration: summarizer → stub LLM → stored summaries
│   ├── test_digest.py       # Integration: digest assembly → DigestReport shape
│   └── test_api.py          # Integration: HTTP → DB → response assertions
├── requirements.txt
└── .env.example

frontend/
├── app/
│   ├── layout.tsx           # Root layout (font, dark mode, nav)
│   ├── page.tsx             # / → redirects or renders latest digest
│   └── reports/
│       └── page.tsx         # /reports → DigestReport view (SSR)
├── components/
│   ├── DigestReport.tsx     # Top-level report container
│   ├── TopicSection.tsx     # Topic group with articles + actionable insight badge
│   ├── ArticleCard.tsx      # Article title, source, bullet summary
│   ├── ActionBadge.tsx      # "Apply" / "Read More" tag, visually distinct
│   ├── FetchButton.tsx      # "Fetch Now" → POST /api/fetch → polls job status
│   └── EmptyState.tsx       # No-digest-yet prompt
├── lib/
│   ├── api.ts               # Typed API client (fetch wrapper)
│   └── types.ts             # TypeScript types mirroring backend Pydantic schemas
├── tests/
│   └── components/
│       ├── DigestReport.test.tsx
│       └── FetchButton.test.tsx
├── package.json
└── .env.local.example
```

---

## Data Flow

### Flow 1: Scheduled / Manual Fetch + Summarize

```
Scheduler / User     --> FastAPI:          POST /api/fetch  (or APScheduler tick)
FastAPI              --> FetchJob:         INSERT status=queued, return job_id
FastAPI              --> BackgroundTask:   enqueue _run_fetch_pipeline(job_id)
_run_fetch_pipeline  --> FetchJob:         UPDATE status=running
_run_fetch_pipeline  --> RSSFetcher:       fetch(source_url) → [RawArticle, ...]
_run_fetch_pipeline  --> NewsAPIFetcher:   fetch(api_key, topics) → [RawArticle, ...]
_run_fetch_pipeline  --> HNFetcher:        fetch() → [RawArticle, ...]
_run_fetch_pipeline  --> Deduplicator:     filter by url_hash UNIQUE → [NewArticle, ...]
_run_fetch_pipeline  --> DB:              INSERT articles (pending)
_run_fetch_pipeline  --> Summarizer:       batch_summarize([NewArticle, ...])
Summarizer           --> LLMClient:        messages=[system_prompt, articles_json]
LLMClient            --> Anthropic API:    POST /v1/messages
Anthropic API        --> LLMClient:        structured JSON {articles:[{id, bullets, topic, insights}]}
Summarizer           --> DB:              UPDATE article summary_status=summarized
Summarizer           --> DB:              INSERT summaries (bullets, topic_tags, insights)
Summarizer           --> DigestAssembler: assemble(summaries) → DigestReport
DigestAssembler      --> DB:              INSERT digest_reports (topic_sections JSON)
_run_fetch_pipeline  --> FetchJob:         UPDATE status=done, articles_added=N
```

### Flow 2: Read Digest (Fast Path)

```
Browser      --> Next.js SSR:      GET /reports
Next.js SSR  --> FastAPI:          GET /api/reports/latest
FastAPI      --> DB:               SELECT digest_reports ORDER BY created_at DESC LIMIT 1
DB           --> FastAPI:          DigestReport row (pre-computed JSON)
FastAPI      --> Next.js SSR:      200 { data: DigestReport }
Next.js SSR  --> Browser:          Rendered HTML (< 2s, no LLM)
```

### Flow 3: Job Status Polling

```
FetchButton  --> FastAPI:    POST /api/fetch → { job_id: "abc123" }
FetchButton  --> FastAPI:    GET /api/jobs/abc123  (every 3s via SWR)
FastAPI      --> DB:         SELECT fetch_jobs WHERE id=abc123
DB           --> FastAPI:    { status: "running", articles_added: null }
FetchButton  --> FastAPI:    GET /api/jobs/abc123  (3s later)
DB           --> FastAPI:    { status: "done", articles_added: 47 }
FetchButton  --> SWR:        mutate("/api/reports/latest")  → UI refreshes digest
```

---

## API Contracts

### GET /api/reports/latest
```json
Response 200:
{
  "data": {
    "id": "uuid",
    "created_at": "2026-03-24T06:00:00Z",
    "article_count": 47,
    "topic_sections": [
      {
        "topic": "AI & Machine Learning",
        "article_count": 12,
        "actionable_insight": {
          "type": "Apply",
          "text": "Try the new Claude tool-use API for your next automation task."
        },
        "articles": [
          {
            "id": "uuid",
            "title": "Anthropic releases Claude 4",
            "source": "TechCrunch",
            "url": "https://...",
            "bullets": [
              "Claude 4 achieves state-of-the-art on coding benchmarks.",
              "New extended context window of 500k tokens.",
              "Available via API today, consumer product next month."
            ]
          }
        ]
      }
    ]
  },
  "error": null,
  "meta": { "generated_at": "2026-03-24T06:02:10Z" }
}

Response 404: { "data": null, "error": "No digest available yet", "meta": {} }
```

### GET /api/reports
```json
Response 200:
{
  "data": [
    { "id": "uuid", "created_at": "2026-03-24T06:00:00Z", "article_count": 47 },
    { "id": "uuid", "created_at": "2026-03-23T06:00:00Z", "article_count": 39 }
  ],
  "error": null,
  "meta": { "total": 2 }
}
```

### POST /api/fetch
```json
Request: {} (empty body)

Response 202:
{
  "data": { "job_id": "uuid", "status": "queued" },
  "error": null,
  "meta": {}
}
```

### GET /api/jobs/{job_id}
```json
Response 200:
{
  "data": {
    "id": "uuid",
    "status": "done",           // queued | running | done | failed
    "started_at": "2026-03-24T10:01:00Z",
    "completed_at": "2026-03-24T10:01:43Z",
    "articles_added": 47,
    "error_message": null
  },
  "error": null,
  "meta": {}
}
```

---

## External Dependencies

### Anthropic Claude API
- **Integration method**: Official `anthropic` Python SDK
- **Auth**: `ANTHROPIC_API_KEY` from env (P10)
- **Model**: `claude-sonnet-4-6` (best balance of cost + quality for structured output)
- **Fallback**: On `APIError` or timeout, articles marked `pending-retry`; existing digest remains visible (SC-006). `StubLLMClient` used in tests (P5).

### NewsAPI.org
- **Integration method**: REST via `httpx`
- **Auth**: `NEWS_API_KEY` from env (P10)
- **Fallback**: Source marked with fetch error; other sources continue (FR-011 pattern). Free tier: 100 req/day — sufficient for 4 fetches/day with 1 request per fetch.

### Hacker News (Algolia API)
- **Integration method**: REST via `httpx` — `https://hn.algolia.com/api/v1/search`
- **Auth**: None required
- **Fallback**: Network error logged; other sources unaffected. Rate limit: 10k req/hour — no concern at 4 fetches/day.

### RSS Feeds (feedparser)
- **Integration method**: `feedparser.parse(url)` — handles RSS 2.0, Atom, RDF
- **Auth**: None (public feeds); Basic Auth support via URL for private feeds if needed
- **Fallback**: `feedparser` returns a `bozo` flag on malformed feeds; logged and skipped.

---

## Open Questions

1. **Prompt tuning**: The batch summarization prompt needs to reliably produce valid JSON from Claude. Should we use `response_format` / tool-use to enforce JSON schema, or rely on prompt instructions? (Recommend: tool-use with a defined `store_digest` tool schema for guaranteed JSON.)
2. **Retry scheduler**: Should `pending-retry` articles be retried automatically on the next scheduled cycle, or only on manual trigger? (Recommend: automatic — re-include in next batch if `summary_status == pending-retry` and age < 48h.)
3. **Article content depth**: Should the fetcher pull full article body (via httpx scraping) or use only the RSS snippet/NewsAPI description? Full body = better summaries but adds scraping complexity. (Recommend: snippet-only for P1; full-body scraping as P2 enhancement.)
4. **Digest granularity**: One digest per fetch cycle, or one per day? If 4 fetches/day, does the user want 4 mini-digests or one merged daily digest? (Recommend: one digest per fetch cycle for P1; daily merge as P2.)
