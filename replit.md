# OrionOS — AI Engineering Operating System

A full production SaaS platform for solo developers. Acts as your CTO, PM, and senior developer assistant — tracking projects, analyzing conversations, scoring project health, generating next steps, running AI agents, and managing subscription billing.

## Run & Operate

- `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000` — run the FastAPI backend
- API docs: http://localhost:8000/docs (Swagger UI)
- Health check: GET /api/v1/healthz

## Stack

- **Runtime**: Python 3.11 + Node.js 20
- **Backend**: FastAPI 0.115 + SQLAlchemy 2.0 (sync) + PostgreSQL
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Billing**: Stripe (optional) — degrades gracefully if keys absent
- **Frontend**: React + Vite + Tailwind + shadcn/ui + wouter
- **API contract**: OpenAPI spec → codegen (Orval) → React Query hooks + Zod schemas

## Where things live

### Backend
- `backend/app/main.py` — FastAPI app entry point, middleware, router registration
- `backend/app/core/config.py` — All settings via pydantic-settings (reads `.env`)
- `backend/app/core/security.py` — JWT creation/decode, bcrypt hash/verify
- `backend/app/core/rate_limiter.py` — In-memory rate limiter (60 req/min/IP)
- `backend/app/db/base.py` — SQLAlchemy declarative base + model imports
- `backend/app/db/session.py` — Engine, session factory, `init_db()`
- `backend/app/db/models/` — User, Project, Message, ProjectStatus, Subscription, CreditLedger, CreditUsageEvent, BillingEvent ORM models
- `backend/app/db/schemas/` — Pydantic request/response schemas
- `backend/app/api/deps.py` — `get_current_user` JWT auth dependency
- `backend/app/api/routes/` — auth, projects, chat, status, github, upload, agents, debug, tasks, billing, dashboard route handlers
- `backend/app/services/ai_service.py` — Rule-based AI analysis engine
- `backend/app/services/status_service.py` — Compute & persist project status
- `backend/app/services/project_service.py` — Project CRUD helpers
- `backend/app/services/credit_service.py` — Credit tracking, plan limits, feature cost deduction
- `backend/app/services/stripe_service.py` — Stripe checkout/portal/webhook integration

### Frontend
- `artifacts/dashboard/src/pages/overview.tsx` — Command-center dashboard (cross-project)
- `artifacts/dashboard/src/pages/billing.tsx` — Subscription, plans, usage history
- `artifacts/dashboard/src/pages/dashboard.tsx` — Projects list
- `artifacts/dashboard/src/pages/project-detail.tsx` — Per-project AI analysis
- `artifacts/dashboard/src/components/credits-widget.tsx` — Header credit meter
- `artifacts/dashboard/src/components/layout.tsx` — Nav (OVERVIEW / PROJECTS / BILLING) + header

### API contract
- `lib/api-spec/openapi.yaml` — Single source of truth for all endpoints
- Codegen: `pnpm --filter @workspace/api-spec run codegen`
- Generated hooks: `lib/api-client-react/src/generated/api.ts`
- Generated Zod schemas: `lib/api-zod/src/generated/api.ts`

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/healthz` | No | Health check |
| POST | `/api/v1/auth/register` | No | Register → JWT |
| POST | `/api/v1/auth/login` | No | Login → JWT |
| GET | `/api/v1/auth/me` | Yes | Current user |
| POST | `/api/v1/projects/` | Yes | Create project |
| GET | `/api/v1/projects/` | Yes | List projects |
| GET | `/api/v1/projects/{id}` | Yes | Get project |
| PATCH | `/api/v1/projects/{id}` | Yes | Update project |
| DELETE | `/api/v1/projects/{id}` | Yes | Delete project |
| POST | `/api/v1/projects/{id}/messages` | Yes | Add chat message |
| GET | `/api/v1/projects/{id}/messages` | Yes | Last 10 messages |
| POST | `/api/v1/projects/{id}/status` | Yes | AI health analysis |
| POST | `/api/v1/projects/{id}/next-steps` | Yes | Prioritized roadmap |
| GET | `/api/v1/projects/{id}/predict` | Yes | Failure prediction |
| POST | `/api/v1/github/connect` | Yes | Connect GitHub repo |
| POST | `/api/v1/github/sync/{id}` | Yes | Sync GitHub commits |
| POST | `/api/v1/upload/{id}` | Yes | Upload ZIP for analysis |
| POST | `/api/v1/agents/{id}` | Yes | Run AI agent team |
| POST | `/api/v1/debug/{id}` | Yes | AI debug engine |
| POST | `/api/v1/tasks/{id}` | Yes | Task breakdown |
| GET | `/api/v1/billing/plans` | No | Get subscription plans |
| GET | `/api/v1/billing/status` | Yes | Plan + credit status |
| GET | `/api/v1/billing/usage` | Yes | Credit usage history |
| POST | `/api/v1/billing/checkout` | Yes | Create Stripe Checkout |
| POST | `/api/v1/billing/portal` | Yes | Create Stripe Portal |
| POST | `/api/v1/billing/cancel` | Yes | Cancel subscription |
| POST | `/api/v1/billing/webhook` | No | Stripe webhook handler |
| GET | `/api/v1/dashboard/overview` | Yes | Command-center overview |

## Subscription Plans (INR)

| Plan | Price | Daily Credits | Monthly Credits |
|------|-------|--------------|-----------------|
| FREE | ₹0 | 25 | 500 |
| PRO | ₹999/mo | 500 | 15,000 |
| TEAM | ₹2,999/mo | 3,000 | 100,000 |

## Credit Costs per Feature

| Feature | Credits |
|---------|---------|
| ZIP Upload | 10 |
| GitHub Sync | 5 |
| AI Agents | 8 |
| Debug / Tasks / Predict / Analysis / Roadmap | 5 each |

## Architecture decisions

- **Sync SQLAlchemy**: keeps connection model simple; no async complexity
- **Rule-based AI engine**: zero external API cost; analyzes message keywords
- **JWT in Bearer header**: stateless auth, no session storage needed
- **In-memory rate limiter**: thread-safe with Lock; 60 req/min/IP
- **Stripe optional**: all billing routes degrade gracefully without Stripe keys
- **Credit system**: deducted per AI feature call; tracked daily + monthly
- **Graceful DB startup**: `init_db()` failure logged but doesn't crash

## Required env vars (backend/.env)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Postgres connection string |
| `SECRET_KEY` | Long random string for JWT signing |
| `ALGORITHM` | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL (default 10080 = 7 days) |
| `STRIPE_SECRET_KEY` | Stripe secret key (optional) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (optional) |
| `STRIPE_PRO_PRICE_ID` | Stripe Price ID for PRO plan (optional) |
| `STRIPE_TEAM_PRICE_ID` | Stripe Price ID for TEAM plan (optional) |

## User preferences

- FastAPI + SQLAlchemy sync stack (strict requirement)
- No async DB operations
- Production-ready security (JWT, bcrypt, rate limiting, ORM-only queries)

## Gotchas

- `DATABASE_URL` must be set before DB tables will be created
- Server starts successfully even without a DB connection (graceful failure)
- Rate limiter is in-memory — resets on process restart
- `backend/.env` is gitignored; use `.env.example` as the template
- Run from `backend/` directory so Python resolves `app.*` imports
- After editing `openapi.yaml`, always run codegen to regenerate hooks
