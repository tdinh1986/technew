# TechNew

A tech news aggregator and summarizer. The Python backend fetches articles from RSS feeds and news APIs, generates AI-powered summaries via Claude, and exposes a REST API. The Next.js frontend displays digest reports and lets you trigger manual fetches.

**How it works:** Fetch articles → deduplicate by URL → summarize with Claude → display bullet-point digest with actionable insights.

---

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=sk-ant-...          # required — get from console.anthropic.com
RSS_FEED_URLS=https://hnrss.org/frontpage,https://feeds.arstechnica.com/arstechnica/index
                                       # required — comma-separated RSS feed URLs
DATABASE_URL=sqlite:///./technew.db   # optional (default shown)
FETCH_INTERVAL_HOURS=6                # optional (default shown)
NEWS_API_KEY=                         # optional — get from newsapi.org
```

Run the database migration, then start the server:

```bash
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local      # sets NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Usage

1. Open the app — you'll see an empty state if no digest exists yet.
2. Click **Fetch & Summarize** to pull the latest articles and generate a digest. This runs in the background; the button polls for completion.
3. The digest appears as topic sections, each with bullet summaries and an actionable insight.
4. Fetches also run automatically every `FETCH_INTERVAL_HOURS` hours.

---

## API Endpoints

All routes are prefixed `/api`. Responses use `{ data, error, meta }` envelope.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/fetch` | Trigger fetch + summarize (returns 202 + job ID) |
| `GET` | `/api/jobs/{id}` | Poll job status (`queued` → `running` → `done`/`failed`) |
| `GET` | `/api/reports/latest` | Latest digest report |
| `GET` | `/api/reports` | Last 30 reports (no topic sections) |

---

## Development

**Backend:**
```bash
cd backend
source .venv/bin/activate
pytest                              # all tests
pytest tests/test_fetcher.py        # single file
pytest -k "test_rss"                # by keyword
ruff check . && ruff format .       # lint + format
```

**Frontend:**
```bash
cd frontend
npm test       # vitest (component tests)
npm run lint   # ESLint
npm run build  # production build check
```

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3.9+, FastAPI, SQLAlchemy 2, Alembic, APScheduler |
| AI | Anthropic SDK (`claude-sonnet-4-6`) |
| Fetching | feedparser, httpx |
| Frontend | Next.js 14 (App Router), Tailwind CSS, SWR |
| Database | SQLite (default) / PostgreSQL (swap via `DATABASE_URL`) |
