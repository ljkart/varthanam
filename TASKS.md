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
- [x] Collection merged articles list
  - pagination
  - sorting

### Background Processing

- [x] Article fetching & storage
- [x] Deduplication strategy (GUID / URL hash)

Status: ✅ COMPLETE

---

## Phase 3 — Reading Experience (User State)

### Models

- [x] UserArticleState

### Endpoints

- [x] Mark read / unread
- [x] Save / unsave
- [x] Filters:
  - unread-only
  - saved-only

### Optional

- [ ] Reader-mode content extraction

Status: ✅ COMPLETE

---

## Phase 4 — Conditional Aggregation (Rules Engine)

### Models

- [x] Rule
- [x] RuleMatch

### API

- [x] Rule CRUD endpoints

### Matching Logic

- [x] Keyword include/exclude matching utility (`app/rules/matcher.py`)
  - Case-insensitive substring matching
  - Include any-of logic
  - Exclude wins over include
  - 35 unit tests covering edge cases

### Workers

- [x] Rule execution task (`run_rule`)
  - `app/workers/rule_runner.py`: Core job function
  - Idempotent via unique constraint check
  - Collection scope support
  - Updates `last_run_at` after run
  - 11 unit tests covering edge cases
- [x] Scheduling via `frequency_minutes`
  - `app/workers/rule_scheduler.py`: Scheduler logic
  - `get_due_rules()`: Find rules due for execution
  - `run_due_rules()`: Execute all due rules with failure handling
  - Respects is_active, frequency_minutes, last_run_at
  - 13 unit tests covering edge cases
- [ ] Time window filtering since `last_run_at` (optional optimization)

Status: ✅ COMPLETE

---

## Phase 5 — Frontend MVP (React SPA + TypeScript)

### Foundation

- [x] React + Vite + TypeScript project setup
- [x] Design tokens from Pencil.ai
- [x] Reusable UI components (Input, Button, Logo)
- [x] Typed API client (`src/lib/api.ts`)
- [x] Auth helpers (`src/lib/auth.ts`)
- [x] React Router configuration

### Core UI

- [x] Auth screens (Login, Register)
  - Matches Pencil.ai design exactly
  - Form validation
  - API integration
  - Error handling
- [x] Collections UI
  - Collections list page with CRUD operations
  - Create/Edit collection modal
  - Delete confirmation modal
  - Loading/Empty/Error states
  - Protected route (requires auth)
  - Comprehensive test coverage (72 tests)
- [x] Feed management UI
  - Feeds page with add/assign operations
  - Add Feed modal with URL validation
  - Assign to Collection modal
  - FeedRow component with status badges
  - useFeeds hook for state management
  - Protected route at /app/feeds
  - Comprehensive test coverage (47 new tests)
- [x] Article list & detail (reader)
  - Dashboard page with sidebar navigation
  - ArticleCard component with summary, author, time ago
  - ArticleReader page for single article view
  - useArticles hook with pagination and filtering
  - Comprehensive test coverage (26 new tests)
- [x] Read / save toggles
  - Mark read/unread functionality
  - Save/unsave functionality
  - Filter by all/unread/saved
  - Visual state indicators on ArticleCard
- [x] Rules UI + matches / digest view
  - RulesPage with CRUD operations
  - RuleCard component with keywords display
  - RuleModal for create/edit
  - useRules hook for state management
  - Toggle rule active/inactive
  - Delete confirmation modal
  - Collection scope selection
  - Comprehensive test coverage (63 new tests)

Status: ✅ COMPLETE

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
