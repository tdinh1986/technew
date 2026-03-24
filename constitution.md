# TechNew Constitution

## Code Quality

### P1 — Single Responsibility Per Module
Each module (`fetcher`, `summarizer`, `scheduler`, `db`) must own exactly one concern. No module may mix data-fetching with persistence or summarization with scheduling. Cross-cutting concerns (logging, error handling) are handled via middleware/decorators, not inline.

### P2 — Pydantic-First Data Contracts
All data moving between layers — HTTP requests, DB rows, LLM responses — must be validated through Pydantic models. No raw dicts passed between modules. FastAPI request/response models are defined separately from DB models.

### P3 — Idempotent Fetch Operations
Article fetching must be idempotent: fetching the same source twice must not create duplicate records. Deduplication key is the article URL hash. This applies to both scheduled and manual triggers.

## Testing Standards

### P4 — Behavior-Driven Integration Tests
Tests assert on observable system behavior (HTTP responses, DB state, rendered UI), not internal implementation. Backend tests use `pytest` + `httpx` against a real in-memory SQLite instance. Frontend tests use `vitest` + `@testing-library/react`. No mocking of database or LLM calls in integration tests; use fixtures and recorded responses.

### P5 — LLM Call Isolation
All Anthropic API calls must be mockable via a `LLMClient` interface injected at startup. Tests use a recorded/stubbed `LLMClient`. This prevents flaky tests and avoids incurring API costs during CI.

## UX Consistency

### P6 — Report-First Information Architecture
The primary view is always the digest report — not a list of articles. Every UI screen serves the goal of fast knowledge catch-up. Actionable insights (what to try, what to read next) are visually distinct from summaries.

### P7 — Readable Typography Over Visual Decoration
Content density is preferred. Long-form summaries render in a comfortable reading width (max ~700px). Tailwind utility classes are used; no custom CSS unless strictly necessary. Dark/light mode respects system preference via `prefers-color-scheme`.

## Performance Benchmarks

### P8 — API Response Budget
- Report list endpoint: < 200ms (data served from DB, no LLM on read path)
- Manual fetch trigger: returns immediately with a job ID; actual fetch is async
- Frontend initial page load: < 2s on a standard connection (Next.js App Router SSR)

### P9 — Background Processing
All fetching and summarization runs out-of-band via APScheduler. The HTTP request/response cycle never blocks on external API calls (RSS, NewsAPI, Anthropic). The frontend polls or subscribes for job status.

## Security Posture

### P10 — Secrets Via Environment Only
`ANTHROPIC_API_KEY`, `NEWS_API_KEY`, and `DATABASE_URL` are loaded exclusively from environment variables via `python-dotenv`. No secrets in code, config files, or logs. The `.env` file is git-ignored.

### P11 — No User-Controlled Shell Execution
The backend must not execute shell commands constructed from user input. URL and topic configurations are stored and used as data, never passed to subprocess calls.

## Governance

Principles are amended by updating this file with a rationale comment and bumping the Last Amended date. Any change that contradicts an existing principle (e.g., adding DB mocks to integration tests) requires an explicit override with documented justification.

**Version**: 1.0 | **Ratified**: 2026-03-24 | **Last Amended**: 2026-03-24
