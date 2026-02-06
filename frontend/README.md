# Varthanam Frontend

A modern, clean React SPA for personal news and content aggregation. Built with React 19, TypeScript, and Vite.

## Overview

Varthanam is a personal news aggregation platform that lets you take control of your information diet. Instead of opaque algorithms deciding what you see, you explicitly control your sources and define rules for content filtering.

### Key Features

- **RSS Feed Aggregation** — Subscribe to any RSS feed and aggregate content in one place
- **Collections** — Organize feeds into themed collections (e.g., "Tech News", "AI & ML")
- **Smart Rules** — Create keyword-based rules to filter and surface relevant content
- **Clean Reading Experience** — Distraction-free article reader with slide-in panel
- **Article State** — Track read/unread status and save articles for later
- **Dark Theme** — Modern dark UI with lime green accents

## Tech Stack

| Category   | Technology                     |
| ---------- | ------------------------------ |
| Framework  | React 19                       |
| Language   | TypeScript 5.9                 |
| Build Tool | Vite 7                         |
| Routing    | React Router 7                 |
| Testing    | Vitest + React Testing Library |
| Styling    | CSS Modules + Design Tokens    |

## Getting Started

### Prerequisites

- Node.js 18+
- npm 9+
- Backend API running (see [backend README](../backend/README.md))

### Installation

```bash
# Clone the repository
git clone https://github.com/ljkart/varthanam.git
cd varthanam/frontend

# Install dependencies
npm ci

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`.

### Environment

The frontend expects the backend API at `http://127.0.0.1:8000`. This is configured in `src/lib/api.ts`.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/              # Base components (Button, Input, Modal)
│   ├── articles/        # Article card, reader panel
│   ├── collections/     # Collection cards and modals
│   ├── feeds/           # Feed management components
│   └── rules/           # Rule cards and modals
├── pages/               # Route page components
│   ├── Home.tsx         # Landing page
│   ├── Login.tsx        # Authentication
│   ├── Register.tsx     # User registration
│   ├── Dashboard.tsx    # Main app dashboard
│   ├── Collections.tsx  # Collection management
│   ├── Feeds.tsx        # Feed management
│   └── Rules.tsx        # Rules management
├── hooks/               # Custom React hooks
│   ├── useArticles.ts   # Article fetching and state
│   ├── useCollections.ts
│   ├── useFeeds.ts
│   └── useRules.ts
├── lib/                 # Utilities and API clients
│   ├── api.ts           # Base API configuration
│   ├── auth.ts          # Authentication context
│   ├── articlesApi.ts   # Articles API client
│   └── ...
├── styles/              # Global styles
│   └── tokens.css       # Design tokens (colors, spacing)
└── test/                # Test utilities
    └── utils.tsx        # Custom render with providers
```

## Available Scripts

| Command                 | Description                         |
| ----------------------- | ----------------------------------- |
| `npm run dev`           | Start development server with HMR   |
| `npm run build`         | Type-check and build for production |
| `npm run preview`       | Preview production build locally    |
| `npm run lint`          | Run ESLint                          |
| `npm run test`          | Run tests in watch mode             |
| `npm run test:run`      | Run tests once                      |
| `npm run test:coverage` | Run tests with coverage report      |

## Testing

Tests are written with Vitest and React Testing Library, following TDD practices.

```bash
# Run all tests
npm run test:run

# Run tests in watch mode
npm run test

# Run with coverage
npm run test:coverage
```

### Test Structure

- Component tests live next to their components (`*.test.tsx`)
- Page tests live in `src/pages/`
- Hook tests live in `src/hooks/`
- Custom test utilities in `src/test/utils.tsx`

**Current coverage: 294 tests passing**

## Design System

The UI follows a modern dark theme with the following design tokens:

### Colors

| Token                    | Value     | Usage                       |
| ------------------------ | --------- | --------------------------- |
| `--color-bg`             | `#000000` | Page background             |
| `--color-card-bg`        | `#0a0a0a` | Card backgrounds            |
| `--color-primary`        | `#bfff00` | Primary accent (lime green) |
| `--color-text-primary`   | `#ffffff` | Primary text                |
| `--color-text-secondary` | `#666666` | Secondary text              |

### Typography

- **Headings**: Inter (system-ui fallback)
- **Body/Mono**: JetBrains Mono

### Components

All components use CSS Modules for scoped styling:

```tsx
import styles from './Button.module.css';

<Button variant="primary">Click me</Button>
<Button variant="secondary">Cancel</Button>
```

## Application Routes

| Route               | Page             | Auth Required |
| ------------------- | ---------------- | ------------- |
| `/`                 | Landing page     | No            |
| `/login`            | Login            | No            |
| `/register`         | Registration     | No            |
| `/app`              | Dashboard        | Yes           |
| `/app/collections`  | Collections      | Yes           |
| `/app/feeds`        | Feed management  | Yes           |
| `/app/rules`        | Rules management | Yes           |
| `/app/articles/:id` | Article reader   | Yes           |

## Features in Detail

### Dashboard

The main dashboard provides:

- **Sidebar navigation** with collapsible menu
- **Filter tabs**: Today, Unread, Saved
- **Collection switching**
- **View modes**: Stacked list or grid view
- **Slide-in article reader** with blur backdrop

### Article Cards

Articles display with:

- Source icon and name
- Title and summary (truncated)
- Author and timestamp
- Save/bookmark actions
- Automatic image extraction from content

### Rules Engine

Create rules with:

- Include/exclude keywords
- Collection scope
- Schedule frequency
- Active/inactive toggle

## API Integration

The frontend communicates with a FastAPI backend. API clients are in `src/lib/`:

```typescript
// Example: Fetch articles
import { articlesApi } from "./lib/articlesApi";

const { articles, total } = await articlesApi.list(collectionId, {
  filter: "unread",
  limit: 20,
  offset: 0,
});
```

## Contributing

1. Follow TDD: Write tests first, then implement
2. Keep components small and focused
3. Use TypeScript strictly (no `any`)
4. Run lint and tests before committing:

```bash
npm run lint && npm run test:run
```

## License

MIT

---

Built with clarity over cleverness. User control over algorithms.
