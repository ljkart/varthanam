# AGENTS.md — Varthanam (Codex Instructions)

This repository follows a strict engineering workflow:

- TDD-first development
- Professional Git + PR workflow
- Mandatory code documentation
- Enforced formatting/linting via pre-commit + CI

Codex MUST:

1. Read ENGINEERING_PLAYBOOK.md and PLANS.md before making changes.
2. Follow TDD: write/adjust tests first, then implement minimal code to pass.
3. Keep changes small, scoped, and PR-ready.
4. Never duplicate rules across docs. ENGINEERING_PLAYBOOK.md is the single source of truth.

---

## Product Context — Varthanam

Varthanam is a **personal news and content aggregation platform**.

### Purpose

- Aggregate news, blogs, and research sources into a single, clean dashboard
- Reduce information overload by letting users explicitly control sources and topics
- Deliver relevant content through **user-defined rules**, not opaque algorithms

### Core Capabilities

- RSS feed aggregation
- User-defined collections (folders of feeds)
- Clean, distraction-free reading experience
- Per-user read / unread and saved state
- Conditional aggregation via rules:
  - keyword-based
  - collection-scoped
  - scheduled execution

### Key Differentiator

- **Rule-based, user-controlled discovery**
- No ranking or recommendations unless explicitly defined by the user
- Predictable, explainable behavior at all times

### Target Users

- Knowledge workers
- Founders and researchers
- Users who want intentional, controllable information intake

### Explicit Non-Goals (Important Constraints)

- This is NOT a social network
- This is NOT an ad-driven recommendation engine
- This is NOT a real-time chat or commenting platform
- Avoid AI summaries, generative rewriting, or personalization unless explicitly planned later

### Guiding Principles

- Clarity over cleverness
- User control over automation
- Explicit rules over hidden heuristics

Codex must keep these product constraints in mind when designing APIs, data models, and workflows.

---

## Project Stack

- Backend: FastAPI (Python)
- DB: PostgreSQL
- Background jobs: Celery + Redis
- Frontend: Next.js (TypeScript)
- Tests: pytest (backend), Jest/Playwright optional (frontend later)

---

## Global Rules (ALL work MUST follow)

### TDD (Non-negotiable)

- Add or update tests BEFORE implementing a feature.
- The goal is: red → green → refactor.
- Every PR must include tests for new behavior unless explicitly documented as "no-test-needed" with justification.

### Documentation (Non-negotiable)

- Public modules/classes/functions must have docstrings (Python) / JSDoc where helpful (TS).
- Document “why” for tricky logic (RSS parsing, deduplication, rule matching).
- Any new endpoint must have:
  - request/response models
  - clear docstring on handler or service function

### Architecture Discipline

- Backend: no business logic in FastAPI routers. Use services/use-cases layer.
- Workers: Celery tasks must be idempotent and safe to retry.
- DB changes: always via migrations (Alembic).
- No breaking API changes without updating tests and documenting impact.

### Scope Control

- Implement ONLY what the current PLANS.md phase/task requires.
- Do not add “nice-to-have” features unless explicitly requested.

---

## Agent Roles (for Codex)

### Architect Agent

Focus:

- Data model, API contracts, sequencing decisions, trade-offs.
  Must:
- Keep design simple and MVP-oriented, no premature optimization.

### Backend Agent

Focus:

- FastAPI API, DB models/migrations, services, auth, validations.
  Must:
- Keep routers thin; ensure strong typing and response models.

### Worker Agent

Focus:

- RSS fetching/parsing, dedup logic, rule engine execution, scheduling.
  Must:
- Idempotency, clear logs, safe retries, partial failure handling.

### Frontend Agent

Focus:

- Next.js UI, clean reading experience, folder/collection views, rule UI.
  Must:
- API-driven UI, accessible and minimal, no backend logic assumptions.

---

## Commands (must keep accurate)

Backend (from repo root):

- Install: `pip install -r backend/requirements.txt` (or your chosen manager)
- Tests: `pytest -q`
- Lint/format: `pre-commit run --all-files`

Frontend (from `frontend/`):

- Install: `npm ci`
- Lint: `npm run lint`
- Tests (if configured): `npm test`

If these commands change, update them in ENGINEERING_PLAYBOOK.md and CI workflow.

---

## Deliverable Format

For each task:

- Provide a short summary of changes
- Include test updates (what was added and why)
- Ensure pre-commit and CI would pass

End.
