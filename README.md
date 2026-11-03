# OrionOS

[![CI](https://github.com/psking004/OrionAi/actions/workflows/ci.yml/badge.svg)](https://github.com/psking004/OrionAi/actions/workflows/ci.yml)

**An AI engineering operating system for solo developers.** OrionOS acts as your CTO, PM and senior-engineer teammate: it tracks your projects, reads your project chat and code, scores project health, predicts failure risks, generates prioritised next steps, runs a team of AI review agents, and meters usage with a credit-based subscription system.

## Features

- **Projects & chat log:** create projects and log progress messages; the engine reads them to understand where a project stands.
- **Health scoring:** a 0–100 health score (`on_track`, `needs_attention`, `at_risk`, `critical`) from detected problems, progress and stuck points.
- **Next steps & task breakdown:** prioritised roadmap and actionable tasks generated per project.
- **Code analysis:** upload a project ZIP or connect and sync a GitHub repo for architecture, issue and risk analysis.
- **AI agent team:** CTO, PM, QA, DevOps and Security agents each review the project and report risks and recommendations.
- **Debug engine & failure prediction:** surfaces likely root causes and upcoming risks.
- **Command-center dashboard:** cross-project overview, per-project analysis, and billing pages.
- **Subscriptions & credits:** Free / Pro / Team plans with daily and monthly credit limits; Stripe Checkout, customer portal and webhooks (optional, the app works without Stripe).
- **Security:** JWT auth, bcrypt password hashing, per-IP rate limiting, request-size limits, ORM-only queries.

## Architecture

```
React dashboard (Vite, :5173)
        │  /api/*
        ▼
Express API gateway (:8080) ── /api/auth, /api/projects ──►  FastAPI backend (:8000) ──► PostgreSQL
        │                                                        │
        └─ /api/healthz (served locally)                         └─ optional: OpenAI, Stripe, GitHub
```

| Part | Path | Stack |
| --- | --- | --- |
| Backend API | `backend/` | Python 3.11, FastAPI, SQLAlchemy 2 (sync), PostgreSQL, Pydantic v2, python-jose, bcrypt, Stripe |
| API gateway | `artifacts/api-server/` | Node.js, Express 5, TypeScript, pino, esbuild |
| Dashboard | `artifacts/dashboard/` | React, Vite, Tailwind CSS, shadcn/ui, TanStack Query, wouter |
| API contract | `lib/api-spec/` | OpenAPI spec → Orval codegen |
| Generated clients | `lib/api-client-react/`, `lib/api-zod/` | React Query hooks and Zod schemas |
| Shared DB schema | `lib/db/` | Drizzle ORM |

The workspace is a pnpm monorepo (`pnpm-workspace.yaml`); the backend is managed with uv (`pyproject.toml`) or pip (`backend/requirements.txt`).

## Requirements

- Node.js 20+ and pnpm 10+ (`corepack enable` or `npm i -g pnpm`)
- Python 3.11+ and [uv](https://docs.astral.sh/uv/) (or pip)
- PostgreSQL (the backend boots without it, but auth and project data need it)

## Setup

```bash
pnpm install                           # JS workspace
uv sync                                # Python backend deps (or: pip install -r backend/requirements.txt)
cp backend/.env.example backend/.env   # set DATABASE_URL and SECRET_KEY
cp .env.example .env                   # optional; all Node values have defaults
```

## Development

Run each in its own terminal:

```bash
RELOAD=1 pnpm dev:backend   # FastAPI on :8000   (python main.py also works)
pnpm dev:api                # Express gateway on :8080, proxies to FastAPI
pnpm dev:web                # Dashboard on :5173, proxies /api to :8080
```

Open http://localhost:5173. FastAPI docs: http://localhost:8000/docs.

After editing `lib/api-spec/openapi.yaml`, regenerate the clients with `pnpm --filter @workspace/api-spec run codegen`.

## Testing and CI

```bash
pnpm run typecheck                          # TypeScript across libs, gateway and dashboard
pnpm build                                  # typecheck + build every package

pip install -r backend/requirements-dev.txt
cd backend && pytest                        # FastAPI tests (TestClient, no database needed)
```

GitHub Actions (`.github/workflows/ci.yml`) runs the frontend typecheck and build and the backend test suite on every push to `main` and every pull request.

## Production

```bash
pnpm install --frozen-lockfile
pnpm build                  # typecheck + build every package
uv sync --frozen

PORT=8000 python main.py    # FastAPI backend (or: uv run main.py)
PORT=8080 pnpm start        # api-server (dist/index.mjs)
```

The dashboard builds to static files in `artifacts/dashboard/dist/public`; serve them from any static host or CDN and route `/api` to the api-server (`pnpm start:web` gives a quick preview server).

## Environment variables

**Backend** (`backend/.env`, template in `backend/.env.example`):

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Long random string for JWT signing (required in production) |
| `ALGORITHM` | JWT algorithm, default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime, default 10080 (7 days) |
| `CORS_ORIGINS` | Allowed origins, default `["*"]` |
| `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW` | Rate limit, default 60 requests per 60 s per IP |
| `DEBUG` | Debug mode, default `false` |
| `OPENAI_API_KEY` | Optional; enables OpenAI-assisted analysis |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID`, `STRIPE_TEAM_PRICE_ID` | Optional; enable Stripe billing |

**Node services** (`.env`, all optional, defaults in `.env.example`): `PORT`, `BASE_PATH`, `FASTAPI_URL`, `FASTAPI_TIMEOUT_MS`, `API_PROXY_TARGET`, `NODE_ENV`. Backend launcher (`main.py`): `HOST`, `PORT`, `RELOAD`.

## API reference (FastAPI)

All protected routes need `Authorization: Bearer <token>`. Full interactive docs at `/docs`.

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/health` | No | Health check |
| POST | `/api/v1/auth/register` | No | Register, returns a JWT |
| POST | `/api/v1/auth/login` | No | Log in, returns a JWT |
| GET | `/api/v1/auth/me` | Yes | Current user |
| GET, POST | `/api/v1/projects/` | Yes | List / create projects |
| GET, PATCH, DELETE | `/api/v1/projects/{project_id}` | Yes | Get / update / delete a project |
| GET, POST | `/api/v1/projects/{project_id}/messages` | Yes | Last 10 messages / add a message |
| POST | `/api/v1/projects/{project_id}/status` | Yes | Health analysis |
| POST | `/api/v1/projects/{project_id}/next-steps` | Yes | Prioritised roadmap |
| GET, DELETE | `/api/v1/projects/{project_id}/github` | Yes | GitHub connection / disconnect |
| POST | `/api/v1/projects/{project_id}/github/connect` | Yes | Connect a GitHub repo |
| POST | `/api/v1/projects/{project_id}/github/sync` | Yes | Sync GitHub commits |
| POST | `/api/v1/projects/{project_id}/upload` | Yes | Upload a ZIP for analysis |
| GET | `/api/v1/projects/{project_id}/uploads`, `/uploads/latest` | Yes | Upload history / latest analysis |
| GET | `/api/v1/projects/{project_id}/agents` | Yes | AI agent team report |
| POST | `/api/v1/projects/{project_id}/debug` | Yes | Debug engine |
| POST | `/api/v1/projects/{project_id}/tasks` | Yes | Task breakdown |
| GET | `/api/v1/projects/{project_id}/predict` | Yes | Failure prediction |
| GET | `/api/v1/billing/plans` | No | Subscription plans |
| GET | `/api/v1/billing/status` | Yes | Plan and credit status |
| GET | `/api/v1/billing/usage` | Yes | Credit usage history |
| POST | `/api/v1/billing/checkout` | Yes | Create a Stripe Checkout session |
| POST | `/api/v1/billing/portal` | Yes | Create a Stripe customer portal session |
| POST | `/api/v1/billing/cancel` | Yes | Cancel subscription |
| POST | `/api/v1/billing/webhook` | No | Stripe webhook (signature verified) |
| GET | `/api/v1/dashboard/overview` | Yes | Command-center overview |

## Plans and credits

| Plan | Price | Daily credits | Monthly credits |
| --- | --- | --- | --- |
| Free | ₹0 | 25 | 500 |
| Pro | ₹499/mo | 500 | 15,000 |
| Team | ₹1,999/mo | 3,000 | 100,000 |

Credit cost per feature: ZIP upload 10, AI agents 8, GitHub sync 5, and 5 each for debug, tasks, prediction, analysis and roadmap.

## Design decisions

- **Sync SQLAlchemy** keeps the connection model simple.
- **Rule-based analysis engine** works with zero external API cost; OpenAI is optional.
- **Stateless JWT auth** in the `Authorization` header.
- **Graceful startup:** the API starts even if the database is unreachable and logs the error.
- **Stripe is optional:** billing routes degrade gracefully without keys.
