# TASKS — Varthanam

This file tracks execution progress against `PLANS.md`.
Each task is completed via a feature branch + PR and must satisfy the
Definition of Done in `PLANS.md` and `ENGINEERING_PLAYBOOK.md`.

---

## Phase 0 — Repo & Tooling Foundation

- [x] Repo structure (backend/ and frontend/)
- [x] Pre-commit configured (Ruff, formatting, hooks)
- [x] CI configured (GitHub Actions)

Status: ✅ COMPLETE

---

## Phase 1 — Backend Foundation (FastAPI + DB + Auth)

### Core Infrastructure

- [x] Health endpoint (+ test)
- [x] FastAPI app structure (routers / services / schemas)
- [x] Backend scaffold (app factory, settings, logging)

### Database & Migrations

- [x] PostgreSQL integration (SQLAlchemy engine + session)
- [x] Alembic setup (alembic.ini, env.py, versions/)
- [x] DB connectivity test (SQLite-based)

### Auth & Users

- [x] User model
- [x] Password hashing utilities
- [x] Alembic migration for users table
- [x] JWT authentication
- [x] Auth endpoints (register / login / me)
- [x] Auth happy-path tests

### Hardening

- [x] Config hardening (env validation, dev/test separation)
- [x] Standardized API error handling
- [x] API versioning (`/api/v1`)

## Phase 2 — Core Aggregation (Feeds, Collections, Articles)

### Models

- [x] Collection
- [x] Feed
- [x] CollectionFeed
- [x] Article

### Endpoints

- [x] CRUD collections
- [x] Add & validate RSS feed
- [x] Assign feed to collection
- [ ] Collection merged articles list
  - pagination
  - sorting

### Background Processing

- [x] Article fetching & storage
- [x] Deduplication strategy (GUID / URL hash)

Status: 🚧 IN PROGRESS

---

## Phase 3 — Reading Experience (User State)

### Models

- [ ] UserArticleState

### Endpoints

- [ ] Mark read / unread
- [ ] Save / unsave
- [ ] Filters:
  - unread-only
  - saved-only

### Optional

- [ ] Reader-mode content extraction

Status: ⏳ NOT STARTED

---

## Phase 4 — Conditional Aggregation (Rules Engine)

### Models

- [ ] Rule
- [ ] RuleMatch

### API

- [ ] Rule CRUD endpoints

### Workers

- [ ] Rule execution task (`run_rule`)
- [ ] Scheduling via `frequency_minutes`
- [ ] Rule matching:
  - include keywords
  - exclude keywords
  - collection scope
  - time window since `last_run_at`

Status: ⏳ NOT STARTED

---

## Phase 5 — Frontend MVP (Next.js)

### Core UI

- [ ] Auth screens
- [ ] Collections UI
- [ ] Feed management UI
- [ ] Article list & detail (reader)
- [ ] Read / save toggles
- [ ] Rules UI + matches / digest view

Status: ⏳ NOT STARTED

---

## Phase 6 — Polish & Production Readiness

### Backend & Workers

- [ ] Feed health tracking
  - failure_count
  - last_fetched_at
- [ ] Structured logs (API + workers)
- [ ] Worker retry behavior (idempotency)

### Platform

- [ ] Rate limits (optional)
- [ ] Caching (optional)
- [ ] Deployment documentation (optional)

Status: ⏳ NOT STARTED
