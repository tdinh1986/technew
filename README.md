# TechNew

A tech news aggregator and summarizer. The Python backend fetches articles from RSS feeds and news APIs, generates AI-powered summaries via Claude, and exposes a REST API. The Next.js frontend displays digest reports and lets you trigger manual fetches.

## Overview

TechNew keeps you caught up on tech news without the noise. Instead of reading dozens of articles, you get a curated daily digest — bullet-point summaries per article plus a high-level overview — all generated automatically.

**How it works:**

1. **Fetch** — Pulls articles from configured RSS feeds and/or NewsAPI; deduplicates by URL hash
2. **Summarize** — Calls Claude (`claude-sonnet-4-6`) to produce per-article bullets and a daily digest
3. **Store** — Persists articles and summaries in SQLite (swappable to PostgreSQL)
4. **Serve** — FastAPI exposes REST endpoints for reports, articles, and manual fetch triggers
5. **Display** — Next.js frontend renders the digest report with actionable insights

## Architecture

```
technew/
├── backend/          # Python (FastAPI)
│   ├── main.py       # FastAPI app entrypoint
│   ├── fetcher.py    # News source fetching (RSS, APIs)
│   ├── summarizer.py # LLM summarization via Anthropic SDK
│   ├── scheduler.py  # APScheduler for periodic fetching
│   ├── models.py     # Pydantic models / DB schemas
│   └── db.py         # SQLite/Postgres via SQLAlchemy
└── frontend/         # Next.js (App Router)
    ├── app/          # Pages and layouts
    ├── components/   # UI components
    └── lib/          # API client, types
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3.12, FastAPI, Uvicorn, APScheduler |
| AI | Anthropic SDK (`claude-sonnet-4-6`) |
| Data | SQLAlchemy, Alembic, SQLite / PostgreSQL |
| Fetching | feedparser, httpx |
| Frontend | Next.js 14 (App Router), Tailwind CSS, SWR |

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Create `backend/.env`:

```
ANTHROPIC_API_KEY=your_key_here
NEWS_API_KEY=your_key_here        # optional
DATABASE_URL=sqlite:///./technew.db
FETCH_INTERVAL_HOURS=6
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

Create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API

All routes are prefixed with `/api`. Responses use a consistent envelope:

```json
{ "data": ..., "error": null, "meta": {} }
```

| Endpoint | Description |
|----------|-------------|
| `GET /api/reports` | List digest reports |
| `GET /api/articles` | List fetched articles |
| `POST /api/fetch` | Trigger a manual fetch (returns job ID immediately) |

## Commands

**Backend:**
```bash
pytest                        # run all tests
pytest tests/test_fetcher.py  # run single test file
ruff check .                  # lint
ruff format .                 # format
```

**Frontend:**
```bash
npm run dev    # development server
npm run build  # production build
npm run lint   # lint
```
