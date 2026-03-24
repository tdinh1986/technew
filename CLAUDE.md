# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TechNew** — a tech news aggregator and summarizer. The Python backend fetches articles from RSS feeds / news APIs, runs summarization (via Claude API), and exposes a REST API. The Next.js frontend displays reports and lets the user trigger fetches.

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

## Backend

### Setup & Run
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Key commands
```bash
pytest                          # run all tests
pytest tests/test_fetcher.py    # run single test file
ruff check .                    # lint
ruff format .                   # format
```

### Environment variables (backend/.env)
```
ANTHROPIC_API_KEY=...
NEWS_API_KEY=...           # optional, for NewsAPI.org
DATABASE_URL=sqlite:///./technew.db
FETCH_INTERVAL_HOURS=6
```

## Frontend

### Setup & Run
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
npm run build && npm start
npm run lint
```

### Environment variables (frontend/.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Data Flow

1. **Fetch** — `fetcher.py` pulls articles from configured RSS feeds and/or NewsAPI; deduplicates by URL hash.
2. **Summarize** — `summarizer.py` calls Claude (`claude-sonnet-4-6`) to produce per-article bullets + a daily digest.
3. **Store** — articles and summaries persisted in DB; reports assembled on read.
4. **Serve** — FastAPI exposes `/api/reports`, `/api/articles`, `/api/fetch` (manual trigger).
5. **Display** — Next.js frontend fetches from the API and renders the digest report with actionable insights.

## API Conventions

- All backend routes prefixed with `/api`
- Responses use consistent envelope: `{ data, error, meta }`
- Frontend API calls live in `frontend/lib/api.ts`

## Key Dependencies

**Backend:** `fastapi`, `uvicorn`, `anthropic`, `feedparser`, `httpx`, `apscheduler`, `sqlalchemy`, `pydantic`, `python-dotenv`

**Frontend:** Next.js 14+ (App Router), Tailwind CSS, `swr` for data fetching
