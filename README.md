# Varthanam

**Personal news and content aggregation platform**

Take control of your information diet. Varthanam lets you aggregate RSS feeds, organize them into collections, and define rules to surface content that matters — no opaque algorithms, just explicit user control.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![React](https://img.shields.io/badge/React-19-61dafb)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178c6)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-009688)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **RSS Feed Aggregation** — Subscribe to any RSS feed and pull content into one place
- **Collections** — Organize feeds into themed folders (e.g., "Tech News", "AI Research")
- **Smart Rules** — Define keyword-based filters to auto-surface or exclude articles
- **Reading State** — Track read/unread status and save articles for later
- **Clean Reader** — Distraction-free slide-in article panel
- **Dark Theme** — Modern UI with lime green accents

## Architecture

```
varthanam/
├── backend/           # FastAPI REST API
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── core/      # Settings, security, logging
│   ├── alembic/       # Database migrations
│   └── tests/         # pytest test suite
│
├── frontend/          # React SPA
│   ├── src/
│   │   ├── pages/     # Route components
│   │   ├── components/# Reusable UI
│   │   ├── hooks/     # Custom React hooks
│   │   ├── lib/       # API clients & utilities
│   │   └── styles/    # Design tokens
│   └── tests/         # Vitest test suite
│
└── .github/workflows/ # CI/CD pipelines
```

## Tech Stack

| Layer        | Technology                                                  |
| ------------ | ----------------------------------------------------------- |
| **Backend**  | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic               |
| **Database** | PostgreSQL                                                  |
| **Frontend** | React 19, TypeScript, Vite, React Router 7                  |
| **Testing**  | pytest (backend), Vitest + React Testing Library (frontend) |
| **Linting**  | Ruff (Python), ESLint (TypeScript)                          |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- Docker (optional, for database)

### 1. Clone the Repository

```bash
git clone https://github.com/ljkart/varthanam.git
cd varthanam
```

### 2. Set Up the Database

```bash
# Using Docker
docker run -d \
  --name varthanam-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=varthanam \
  -p 5432:5432 \
  postgres:14

# Or use an existing PostgreSQL instance
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

**Environment Variables:**

| Variable                          | Description                  | Default                                                            |
| --------------------------------- | ---------------------------- | ------------------------------------------------------------------ |
| `DATABASE_URL`                    | PostgreSQL connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/varthanam` |
| `JWT_SECRET_KEY`                  | Secret for JWT tokens        | `change-me` (change in production!)                                |
| `JWT_ALGORITHM`                   | JWT signing algorithm        | `HS256`                                                            |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry                 | `60`                                                               |

### 4. Start the Backend

```bash
# Install dependencies
uv sync  # or: pip install -e .

# Run database migrations
DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/varthanam" \
JWT_SECRET_KEY="your-secret" \
uv run alembic upgrade head

# Start the server
DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/varthanam" \
JWT_SECRET_KEY="your-secret" \
uv run uvicorn app.main:app --reload --app-dir backend
```

The API will be available at `http://127.0.0.1:8000`.

API docs: `http://127.0.0.1:8000/docs`

### 5. Start the Frontend

```bash
cd frontend
npm ci
npm run dev
```

The app will be available at `http://localhost:5173`.

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Endpoint                     | Method           | Description                |
| ---------------------------- | ---------------- | -------------------------- |
| `/health`                    | GET              | Health check               |
| `/auth/register`             | POST             | Register new user          |
| `/auth/login`                | POST             | Login, get JWT token       |
| `/collections`               | GET, POST        | List/create collections    |
| `/collections/{id}`          | GET, PUT, DELETE | Collection CRUD            |
| `/collections/{id}/feeds`    | GET, POST        | Manage collection feeds    |
| `/collections/{id}/articles` | GET              | Get articles in collection |
| `/feeds`                     | GET, POST        | List/add RSS feeds         |
| `/feeds/{id}`                | GET, DELETE      | Feed details/removal       |
| `/articles/{id}/read`        | POST             | Mark article as read       |
| `/articles/{id}/unread`      | POST             | Mark article as unread     |
| `/articles/{id}/save`        | POST             | Save article               |
| `/articles/{id}/unsave`      | POST             | Unsave article             |
| `/rules`                     | GET, POST        | List/create rules          |
| `/rules/{id}`                | GET, PUT, DELETE | Rule CRUD                  |
| `/rules/{id}/toggle`         | POST             | Enable/disable rule        |

## Development

### Running Tests

**Backend:**

```bash
# Run all tests
uv run pytest -q

# Run with coverage
uv run pytest --cov=app
```

**Frontend:**

```bash
cd frontend

# Run all tests
npm run test:run

# Run in watch mode
npm run test

# Run with coverage
npm run test:coverage
```

### Code Quality

```bash
# Backend: lint and format
pre-commit run --all-files

# Frontend: lint
cd frontend && npm run lint
```

### Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Check current version
uv run alembic current
```

## Project Structure

### Backend Models

| Model              | Description                            |
| ------------------ | -------------------------------------- |
| `User`             | User accounts with email/password auth |
| `Collection`       | User-created feed folders              |
| `Feed`             | RSS feed subscriptions                 |
| `CollectionFeed`   | Many-to-many: collections ↔ feeds      |
| `Article`          | Fetched articles from feeds            |
| `UserArticleState` | Per-user read/saved state              |
| `Rule`             | Keyword-based filter rules             |
| `RuleMatch`        | Articles matched by rules              |

### Frontend Pages

| Route              | Component     | Description         |
| ------------------ | ------------- | ------------------- |
| `/`                | `Home`        | Landing page        |
| `/login`           | `Login`       | Authentication      |
| `/register`        | `Register`    | User registration   |
| `/app`             | `Dashboard`   | Main feed reader    |
| `/app/collections` | `Collections` | Manage collections  |
| `/app/feeds`       | `Feeds`       | Manage RSS feeds    |
| `/app/rules`       | `Rules`       | Manage filter rules |

## Design Principles

- **Clarity over cleverness** — Simple, readable code
- **User control over algorithms** — No hidden recommendations
- **Explicit rules over heuristics** — Users define what they see
- **TDD-first development** — Tests before implementation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests first (TDD)
4. Implement the feature
5. Ensure all tests pass and linting is clean
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow TDD: write tests before implementation
- Keep PRs small and focused
- Use conventional commits
- Ensure CI passes before merging

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Varthanam** (വർത്തനം) — Malayalam for "news" or "tidings"
