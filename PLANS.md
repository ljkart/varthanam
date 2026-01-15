# PLANS.md — Varthanam Development Plan (TDD-gated)

This plan is intentionally phased. Each phase has a TDD gate:

- Tests written/updated
- Implementation done
- Refactor with tests green
- CI passing

---

## Phase 0 — Repo & Tooling Foundation

Goals:

- Repo structure: backend/ and frontend/
- Pre-commit configured
- CI configured

TDD Gate:

- CI runs and passes on empty baseline (or minimal smoke tests)

---

## Phase 1 — Backend Foundation (FastAPI + DB + Auth)

Deliverables:

- FastAPI app structure (routers/services/schemas)
- PostgreSQL integration
- Alembic setup
- JWT auth + user model
- Health endpoint

TDD Gate (must exist):

- Health endpoint test
- Auth: register/login happy-path tests
- DB connectivity test (or service layer test)

---

## Phase 2 — Core Aggregation (Feeds, Collections, Articles)

Deliverables:

- Models: Collection, Feed, CollectionFeed, Article
- Endpoints:
  - CRUD collections
  - Add/validate RSS feed
  - Assign feed to collection
  - Collection merged articles list (pagination + sorting)
- Dedup strategy (guid/url hash)

TDD Gate:

- Add feed validates RSS URL and stores normalized feed data
- Fetching inserts articles and deduplicates correctly
- Collection articles endpoint returns expected ordering + pagination

---

## Phase 3 — Reading Experience (User state)

Deliverables:

- UserArticleState model
- Endpoints:
  - Mark read/unread
  - Save/unsave
  - Filters: unread-only, saved-only
- Optional: reader mode on-demand extraction

TDD Gate:

- Read/unread state is per-user and persists
- Saved state is per-user and persists
- Filters work and are performant (indexed queries)

---

## Phase 4 — Conditional Aggregation (Rules Engine)

Deliverables:

- Models: Rule, RuleMatch
- Rule CRUD endpoints
- Worker task: run_rule(rule_id)
- Schedules based on frequency_minutes
- Matching: include/exclude keywords, collection scope, time window since last_run_at

TDD Gate:

- Keyword include/exclude matching unit tests (edge cases)
- Rule run stores matches and avoids duplicates
- Scheduling behavior respects frequency and last_run_at

---

## Phase 5 — Frontend MVP (Next.js)

Deliverables:

- Auth screens
- Collections UI
- Feed management UI
- Article list + detail (reader)
- Read/save toggles
- Rules UI + matches/digest view

TDD Gate:

- Frontend lint passes
- Basic UI smoke tests (optional)
- No broken API contract (manual or contract tests)

---

## Phase 6 — Polish & Production Readiness

Deliverables:

- Feed health (failure_count, last_fetched_at)
- Observability: structured logs for workers + API
- Rate limits, caching (optional)
- Deployment docs (optional)

TDD Gate:

- Failure handling tests for feed fetching
- Worker retry behavior tests (idempotency)
- CI green, pre-commit clean

---

## Definition of Done (applies to every phase/task)

- Tests added/updated
- Docstrings/comments for non-trivial logic
- Lint/format checks pass locally
- CI passes
- PR-ready (small, reviewed, clear)
