# Feature Specification: Tech News Aggregator & Digest

**Feature Branch**: `002-tech-news-aggregator`
**Created**: 2026-03-24
**Status**: Draft

---

## User Scenarios & Testing

### User Story 1 — Read Today's Digest (Priority: P1)

As a tech professional, I open the app and immediately see a curated, AI-generated digest of what happened in tech today, grouped by topic, with clear summaries and at least one "what to do about it" insight per topic — so I can stay current in under 10 minutes.

**Why this priority**: This is the entire value proposition. Without a readable, insightful digest, the app has no reason to exist.

**Independent Test**: Can be fully tested by pre-loading the DB with fixture articles + summaries and visiting `/reports` — the digest renders without triggering a fetch or LLM call.

**Acceptance Scenarios**:

```gherkin
Feature: Daily Digest Report

  Scenario: View the latest digest report
    Given the system has fetched and summarized articles
    And the user opens the app
    When the user navigates to the Reports page
    Then the daily digest is displayed with a summary headline
    And each topic section lists key takeaways
    And actionable insights are visually highlighted

  Scenario: No digest available yet
    Given no fetch has been run
    When the user opens the Reports page
    Then an empty state is shown with a prompt to trigger a fetch
```

---

### User Story 2 — Fetch News from Multiple Sources (Priority: P1)

As a user, I want the system to automatically collect articles from RSS feeds, NewsAPI, and Hacker News on a configurable schedule, with no duplicates, so I always have fresh content without manual work.

**Why this priority**: No content = no digest. Fetching is the foundation of everything else.

**Independent Test**: Can be tested by running `POST /api/fetch` in isolation against fixture feed data and asserting DB state — no LLM or frontend needed.

**Acceptance Scenarios**:

```gherkin
Feature: Multi-Source News Fetching

  Scenario: Fetch from all configured sources on schedule
    Given RSS feeds, NewsAPI, and Hacker News sources are configured
    And the scheduler interval has elapsed
    When the scheduler triggers a fetch job
    Then articles are collected from all active sources
    And duplicate articles are deduplicated by URL hash
    And new articles are persisted to the database
    And a fetch-complete event is recorded with timestamp

  Scenario: Manual fetch trigger
    Given the user is on the dashboard
    When the user clicks Fetch Now
    Then a fetch job is enqueued and a job ID is returned
    And the UI shows a loading indicator
    And the UI updates when the job completes

  Scenario: Source is unreachable
    Given one news source returns a network error
    When the fetch job runs
    Then the error is logged with source name
    And other sources continue fetching normally
    And no partial data is lost
```

---

### User Story 3 — AI Summarization with Actionable Insights (Priority: P1)

As a user, I want each batch of fetched articles summarized into concise bullet points, grouped by topic, and enhanced with at least one actionable "apply this" or "read more" tag — so I know not just what happened but what I should do.

**Why this priority**: Raw article titles are not enough. The AI layer is what transforms news into knowledge.

**Independent Test**: Can be tested by calling the summarizer module directly with fixture articles and asserting summary structure — no frontend or scheduler needed.

**Acceptance Scenarios**:

```gherkin
Feature: AI Summarization and Actionable Insights

  Scenario: Summarize a batch of articles into a digest
    Given new articles have been fetched and stored
    And the summarizer job is triggered
    When the LLM processes the article batch
    Then each article has a 3-5 bullet summary
    And a digest section groups articles by topic
    And each topic includes at least one actionable insight tagged with Apply or Read More
    And summaries are stored and linked to the source articles

  Scenario: Article already summarized
    Given an article already has a stored summary
    When the summarizer job processes the same article
    Then the existing summary is reused
    And no duplicate LLM call is made

  Scenario: LLM call fails
    Given the Anthropic API returns an error
    When the summarizer attempts to process an article
    Then the error is logged
    And the article is marked as pending-retry
    And the job continues processing remaining articles
```

---

### User Story 4 — Configure Sources and Topics (Priority: P2)

As a user, I want to add, remove, and toggle RSS feeds and topic keywords from a settings screen, so the digest stays relevant to what I actually care about.

**Why this priority**: Without config, all users get the same hardcoded feeds. This makes the app personal and useful over time.

**Independent Test**: Can be tested by calling `POST /api/sources` and `GET /api/sources` and asserting CRUD behavior — no fetch or LLM needed.

**Acceptance Scenarios**:

```gherkin
Feature: Source and Topic Configuration

  Scenario: Add a new RSS feed source
    Given the user is on the Settings page
    When the user enters a valid RSS feed URL and saves
    Then the source appears in the active sources list
    And the next scheduled fetch includes this source

  Scenario: Add a topic of interest
    Given the user is on the Settings page
    When the user enters a topic keyword and saves
    Then new digests filter and prioritize articles matching the topic
    And the topic tag appears in digest sections

  Scenario: Disable a source
    Given a source is listed as active
    When the user toggles the source off
    Then the source is marked inactive
    And future fetch jobs skip this source
    And existing articles from this source are preserved

  Scenario: Invalid RSS URL
    Given the user enters a malformed URL
    When the user tries to save the source
    Then a validation error is shown
    And no source is created
```

---

### Edge Cases

- What happens when the same article URL appears across two different sources (e.g., syndicated to both RSS and NewsAPI)?
  → Deduplicated by URL hash; only one record stored, attributed to the first source that fetched it.
- What happens when the LLM returns a malformed or empty summary?
  → Article flagged `pending-retry`; a fallback one-sentence summary is extracted from the article's own description field and shown in the UI until retry succeeds.
- What happens if the scheduled fetch overlaps with a manually triggered fetch?
  → The second job queues and runs only after the first completes; concurrent fetches for the same source are prevented by a job-status lock.
- What happens when there are no new articles since the last fetch?
  → The previous digest remains visible; no new digest is generated; the fetch-complete event records "0 new articles".
- What happens if a topic keyword matches nothing?
  → The topic tag still appears in settings; the digest shows "No articles matched this topic today" in that section.

---

## Requirements

### Functional Requirements

- **FR-001**: The system MUST fetch articles from at minimum three source types: RSS feeds, NewsAPI, and Hacker News.
- **FR-002**: The system MUST deduplicate articles by URL hash before persisting.
- **FR-003**: The system MUST generate a per-article summary of 3–5 bullet points using an LLM.
- **FR-004**: The system MUST group article summaries into a digest organized by topic.
- **FR-005**: The system MUST include at least one actionable insight per topic section, tagged as "Apply" or "Read More".
- **FR-006**: The system MUST run fetch-and-summarize jobs on a user-configurable schedule (default: every 6 hours).
- **FR-007**: The system MUST allow the user to manually trigger a fetch at any time without blocking the HTTP response.
- **FR-008**: The system MUST allow adding, editing, disabling, and deleting news sources via a settings interface.
- **FR-009**: The system MUST allow the user to define topic keywords that filter and prioritize digest content.
- **FR-010**: The system MUST skip LLM summarization for articles that already have a stored summary.
- **FR-011**: The system MUST continue processing remaining articles when a single LLM call fails.
- **FR-012**: The system MUST validate RSS feed URLs before saving a new source.
- **FR-013**: The frontend MUST display the digest in a readable, scannable format with distinct visual treatment for actionable insights.
- **FR-014**: The system MUST persist all articles, summaries, and reports to a database to serve them without re-calling the LLM on every read.

### Key Entities

- **Article**: `url` (unique hash key), `title`, `source_id`, `fetched_at`, `raw_content`, `summary_status` (`pending` | `summarized` | `pending-retry`).
- **Summary**: `article_id`, `bullets` (list of 3–5 strings), `topic_tags`, `actionable_insights`.
- **DigestReport**: `created_at`, `topic_sections`, `article_count`. Assembled view; not re-computed on every read.
- **Source**: `type` (`rss` | `newsapi` | `hackernews`), `url`, `enabled`, `last_fetched_at`.
- **TopicFilter**: `keyword`, `active`, `created_at`.
- **FetchJob**: `status` (`queued` | `running` | `done` | `failed`), `started_at`, `completed_at`, `articles_added`.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A user can read the digest and identify ≥ 3 relevant topics in under 10 minutes.
- **SC-002**: The report page loads in < 2 seconds (SSR from DB; no LLM on read path).
- **SC-003**: A manual fetch triggered via the UI completes and the updated digest appears within 60 seconds for 5 standard sources.
- **SC-004**: Zero duplicate articles appear in the digest across back-to-back fetches of the same sources.
- **SC-005**: Adding a new RSS source and seeing it in the next digest requires ≤ 3 user interactions on the settings page.
- **SC-006**: When the LLM is unavailable, the app continues to display the previously generated digest with no crash or blank screen.

### Definition of Done

- [ ] All FR-001–FR-014 requirements have passing integration tests
- [ ] All BDD scenarios pass (happy path + error cases)
- [ ] `ruff check` and `ruff format` pass with zero warnings
- [ ] `npm run lint` passes on frontend
- [ ] Constitution compliance verified (P1–P11 checked against plan)
- [ ] Digest renders correctly on mobile viewport (375px)
- [ ] `.env.example` files exist for both backend and frontend
