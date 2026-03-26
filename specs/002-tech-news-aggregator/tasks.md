# Tasks: Tech News Aggregator & Digest (P2 — Source & Topic Configuration)

**Branch**: `002-tech-news-aggregator` | **Date**: 2026-03-25 | **Plan**: `specs/002-tech-news-aggregator/plan.md` (P2 plan at `~/.claude/plans/magical-hugging-platypus.md`)

> **Scope**: P2 only — User Story 4 (Configure Sources and Topics). P1 tasks (T001–T041) are in git history.
> Within each milestone, all `[P]` tasks are fully parallel and independent. Milestones 2 and 3 are parallel with each other once Milestone 1 is complete.

---

## Milestone 1 — Foundational Contracts
*Schema + migration changes that every other task depends on. Complete this milestone entirely before starting anything else.*

- [x] [T001] [P] Add `TopicFilter` ORM model — fields: `id` (UUID PK), `keyword` (str, unique), `active` (bool, default=True), `created_at` (datetime); import and register in `Base` (`backend/models/orm.py`)

- [x] [T002] [P] Add Source + Topic Pydantic v2 schemas — `SourceOut` (id, type, url, name, enabled, last_fetched_at), `SourceCreate` (type, url, name optional), `SourceUpdate` (enabled optional, url optional), `TopicFilterOut` (id, keyword, active, created_at), `TopicFilterCreate` (keyword) — all wrapped in `ApiResponse[T]` pattern (`backend/models/schemas.py`)

- [x] [T003] [P] Create Alembic migration 002 — adds `topic_filters` table with columns matching `TopicFilter` ORM; also adds optional `name` column to existing `sources` table (`backend/alembic/versions/002_add_topic_filters.py`)

- [x] [T004] [P] Add TypeScript types — `Source` (id, type, url, name, enabled, last_fetched_at), `SourceCreate`, `SourceUpdate`, `TopicFilter` (id, keyword, active, created_at), `TopicFilterCreate` — export as named types (`frontend/lib/types.ts`)

---

## Milestone 2 — Source Management API (FR-008, FR-012)
*All tasks [P]. Requires Milestone 1. Covers the full source CRUD API and fetch pipeline refactor.*

- [x] [T005] [P] [US4] Create sources API router — `POST /api/sources` (feedparser validate: `bozo==False` and `len(entries)>0`; auto-populate `name` from `feed.title`; return 422 on invalid feed), `GET /api/sources` (list all with `meta.total`), `PATCH /api/sources/{id}` (update enabled/url; 404 if not found), `DELETE /api/sources/{id}` (soft-disable: set `enabled=False`; no row deleted per constitution rule 4) (`backend/api/sources.py`)

- [x] [T006] [P] [US4] Refactor fetch pipeline — modify `_run_fetch_pipeline` to: (1) query `Source WHERE enabled=True` from DB instead of `settings.rss_feeds`; (2) instantiate `RSSFetcher([s.url for s in rss_sources])`, `HNFetcher()`, `NewsAPIFetcher(api_key)` based on source type; (3) populate `article.source_id` when inserting new articles (`backend/api/fetch.py`)

- [x] [T007] [P] [US4] Write sources integration tests — assert: (1) `POST /api/sources` with valid RSS URL inserts and returns `SourceOut`; (2) `POST /api/sources` with malformed URL returns 422; (3) `POST /api/sources` with empty-feed URL returns 422; (4) `PATCH /api/sources/{id}` with `enabled=False` disables without deleting row; (5) `GET /api/sources` lists all sources including disabled ones; (6) `DELETE /api/sources/{id}` sets `enabled=False` and source row still exists in DB (`backend/tests/test_sources.py`)

---

## Milestone 3 — Topic Configuration (FR-009)
*All tasks [P]. Requires Milestone 1. Parallel with Milestone 2.*

- [x] [T008] [P] [US4] Create topics API router — `POST /api/topics` (insert `TopicFilter`; 409 if keyword already exists), `GET /api/topics` (list all active + inactive with `meta.total`), `DELETE /api/topics/{id}` (hard delete — no FK dependents) (`backend/api/topics.py`)

- [x] [T009] [P] [US4] Modify digest assembler — on `assemble_digest()`: (1) query `TopicFilter WHERE active=True`; (2) for each article, check `title + raw_content[:500]` case-insensitively against each keyword; (3) assign `matched_topic = first matching keyword` or fall back to `topic_tags[0]` from LLM summary; (4) group sections by matched_topic (keyword-matched sections first, then LLM-grouped fallbacks) (`backend/digest.py`)

- [x] [T010] [P] [US4] Write topics integration tests — assert: (1) `POST /api/topics` creates a `TopicFilter` and returns `TopicFilterOut`; (2) duplicate keyword returns 409; (3) `GET /api/topics` lists all filters; (4) `DELETE /api/topics/{id}` removes the row (hard delete confirmed) (`backend/tests/test_topics.py`)

---

## Milestone 4 — App Assembly
*Single wiring task. Requires Milestones 2 + 3 (router files must exist to be imported).*

- [x] [T011] [depends: T005, T006, T008, T009] [US4] Wire routers + bootstrap seed — in `backend/main.py` lifespan: (1) after `init_db()`, call `seed_sources_from_config(db, settings)` if `sources` table is empty (insert RSS URLs from `settings.rss_feeds`, HN source, NewsAPI source if key set); (2) register `api/sources.py` and `api/topics.py` routers under `/api` prefix (`backend/main.py`)

---

## Milestone 5 — Frontend Components
*T012–T015 are all [P] and independent of each other. T016 (settings page) requires T012–T015. Requires Milestone 1 (types.ts).*

- [x] [T012] [P] [US4] Add frontend API helpers — `getSources(): Promise<ApiResponse<Source[]>>`, `createSource(body: SourceCreate)`, `updateSource(id, body: SourceUpdate)`, `deleteSource(id)`, `getTopics()`, `createTopic(body: TopicFilterCreate)`, `deleteTopic(id)` — all use existing `apiFetch<T>` wrapper (`frontend/lib/api.ts`)

- [x] [T013] [P] [US4] `SourceList` component — client component; fetches sources via `getSources()` with SWR; renders a list of source rows (name/url, type badge, enabled toggle via `updateSource`, delete button via `deleteSource`); inline add-form with URL input; calls `createSource` on submit, shows inline validation error on 422; optimistic UI update on toggle (`frontend/components/SourceList.tsx`)

- [x] [T014] [P] [US4] `TopicList` component — client component; fetches topics via `getTopics()` with SWR; renders keyword pills with delete button (`deleteTopic`); inline add-form with keyword text input; calls `createTopic` on submit; shows 409 error inline on duplicate (`frontend/components/TopicList.tsx`)

- [x] [T015] [P] [US4] Add "Settings" nav link — add `<Link href="/settings">Settings</Link>` to top nav alongside existing app title and `FetchButton`; no layout changes beyond the nav link addition (`frontend/app/layout.tsx`)

- [x] [T016] [depends: T012, T013, T014] [US4] Settings page — async server component; renders `<SourceList />` and `<TopicList />` in a two-section layout with headings "News Sources" and "Topic Filters"; uses `max-w-2xl mx-auto` prose container (P7); no SSR data-fetch (components are client-side via SWR) (`frontend/app/settings/page.tsx`)

---

## Milestone 6 — Tests & Polish
*All tasks [P]. Run after all milestones complete.*

- [x] [T017] [P] [US4] Frontend component tests — write vitest + @testing-library/react tests: (1) `SourceList` renders seeded sources, shows toggle and delete buttons, renders validation error on 422 mock; (2) `TopicList` renders keyword pills, shows 409 error on duplicate mock (`frontend/tests/components/SourceList.test.tsx`, `frontend/tests/components/TopicList.test.tsx`)

- [x] [T018] [P] [US4] Extend digest tests for topic matching — add test cases to `test_digest.py`: (1) when a `TopicFilter` keyword matches an article title, the article appears in a keyword-named section; (2) when no keyword matches, article falls back to LLM-assigned topic tag; (3) keyword-matched sections appear before unmatched sections in `topic_sections` (`backend/tests/test_digest.py`)

---

## Dependency Map

```
Milestone 1: T001, T002, T003, T004 [all parallel]
  └─► Milestone 2: T005, T006, T007 [all parallel; T005+T006 need T001+T002; T007 needs T005]
  └─► Milestone 3: T008, T009, T010 [all parallel; T008+T009 need T001+T002; T010 needs T008]

Milestones 2 + 3 are parallel with each other.

Milestone 4: T011 [after T005, T006, T008, T009]
  └─► (T007, T010 can still run in parallel with T011)

Milestone 1 (T004 only):
  └─► Milestone 5: T012, T013, T014, T015 [all parallel]
        └─► T016 [after T012, T013, T014]

Milestone 6: T017, T018 [parallel; T017 after T013+T014; T018 after T009]
```

---

## Implementation Strategy

**Recommended sequence for a solo developer**:

1. **Session 1** — Complete Milestone 1 entirely (T001–T004). All future work depends on these schema changes.
2. **Session 2** — Run Milestones 2 + 3 in parallel: sources API (T005–T007) in one window, topics API + digest (T008–T010) in another.
3. **Session 3** — Milestone 4 wiring (T011) — quick once the routers exist. Then Milestone 5 frontend (T012–T016) in parallel.
4. **Session 4** — Milestone 6 tests + lint gate (T017–T018), then BDD acceptance walkthrough.

**For parallel team**: Milestones 2 and 3 can be assigned to separate developers simultaneously after Milestone 1 merges.

---

## Definition of Done Checklist

- [ ] All P2 BDD scenarios from `spec.md` pass end-to-end (US4: add/disable source, add topic, invalid URL rejected)
- [ ] `pytest backend/` passes with zero failures (including T007, T010, T018)
- [ ] `npm run test` passes with zero failures (including T017)
- [ ] `ruff check backend/` → zero warnings
- [ ] `npm run lint` → zero warnings
- [ ] `POST /api/sources` with valid RSS URL responds in < 2s (including feedparser validation)
- [ ] `GET /api/sources` responds in < 200ms
- [ ] Adding a new RSS source and seeing it in the next digest requires ≤ 3 UI interactions (SC-005)
- [ ] Disabled source rows still exist in DB (soft-disable verified)
- [ ] Topic keyword sections appear correctly grouped in digest after a fetch cycle
