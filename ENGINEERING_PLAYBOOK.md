# ENGINEERING_PLAYBOOK.md — Varthanam

This is the single source of truth for engineering rules:

- TDD approach
- Git workflow
- Documentation requirements
- Coding standards
- How to run checks

AGENTS.md references this file. Do not duplicate these rules elsewhere.

---

## 1) Development Principles

- Build MVP first, scale later.
- Prefer clarity over cleverness.
- Fail loudly but gracefully (good error messages, safe retries in workers).
- Keep routers thin; business logic belongs in services/use-cases.

---

## 2) TDD Policy

### Required workflow

1. Write failing tests for the behavior change.
2. Implement the smallest change to make tests pass.
3. Refactor with tests green.
4. Add edge-case tests if logic is non-trivial.

### What must be tested

Backend:

- Endpoint behavior (integration-ish tests with test client)
- Service layer logic (unit tests) for:
  - RSS normalization
  - Deduplication
  - Rule matching
    Workers:
- Idempotency: repeated runs do not duplicate records
- Failure behavior: retries do not corrupt state

Frontend:

- Lint is mandatory.
- UI tests are optional initially but encouraged for critical flows.

---

## 3) Git Workflow (Professional PR-based)

### Branching

- main: always deployable
- Feature branches:
  - feature/<short-kebab-case>
- Bugfix branches:
  - fix/<short-kebab-case>
- Chores:
  - chore/<short-kebab-case>

### Commits (Conventional Commits)

Use:

- feat: new feature
- fix: bug fix
- test: tests only
- refactor: refactor without behavior change
- chore: tooling/docs/deps

Examples:

- feat: add rss feed validation
- test: cover rule keyword matching edge cases
- fix: prevent duplicate articles when guid missing

### PR Rules

A PR must:

- Include tests for new behavior
- Pass CI
- Keep changes focused (avoid unrelated refactors)
- Update docstrings/comments for non-trivial logic
- Include screenshots for UI changes

Merging:

- Squash merge into main
- Delete branch after merge

---

## 4) Documentation Policy

### Python (FastAPI / Workers)

Docstrings:

- Required for all public modules, classes, functions.
- Use Google-style docstrings.
- Include:
  - Summary line
  - Args / Returns
  - Raises (when relevant)

Comments:

- Explain "why", not "what".
- Required for tricky parsing, dedup, and matching logic.

API endpoints:

- Must have explicit request/response models (Pydantic).
- Ensure response_model is set for FastAPI routes.

### TypeScript (Next.js)

- Prefer readable components and hooks.
- Use JSDoc for complex utilities/hook logic where it clarifies intent.
- Keep components small and composable.

---

## 5) Coding Standards & Tooling

### Backend (Python)

Target:

- Python 3.11+

Style:

- Follow modern Python practices + type hints.
- Avoid implicit Any for public functions.

Tooling (enforced via pre-commit + CI):

- Ruff for linting
- Ruff formatter or Black (choose one; this repo uses Ruff formatter)
- pytest for tests

### Frontend (Next.js)

Target:

- Node 20+
- TypeScript strict mode (recommended)

Tooling:

- ESLint (Next.js recommended)
- Prettier (recommended)

---

## 6) Error Handling & Reliability

### RSS fetching and parsing

- Validate feeds on add (basic network + parse validation).
- Normalize published dates; handle missing fields safely.
- Deduplicate consistently using a stable hash strategy.

### Celery tasks

- Must be idempotent.
- Safe to retry:
  - No duplicate inserts
  - Uses upserts or uniqueness constraints
- Log start/end and key counters (articles fetched/created/skipped).

---

## 7) Local Commands (must stay accurate)

### Pre-commit

From repo root:

- Install hooks: `pre-commit install`
- Run all: `pre-commit run --all-files`

### Backend

- Tests: `pytest -q`
- (Optional) coverage: `pytest --cov=backend`

### Frontend

From `frontend/`:

- Install: `npm ci`
- Lint: `npm run lint`
- Build: `npm run build`

---

## 8) “Definition of Done” Checklist

- [ ] Tests added/updated
- [ ] All backend tests pass locally using `uv run pytest -q`
- [ ] Run `uv run pre-commit run --all-files` and fixes all errors if any
- [ ] Docstrings/comments added where needed
- [ ] Lint/format passes (pre-commit)
- [ ] CI passes
- [ ] PR description created using the repository PR template (Markdown)
- [ ] TASKS.md updated to reflect completed tasks
