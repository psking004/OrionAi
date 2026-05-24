# AI Teammate for Solo Developers

An AI-powered productivity platform that acts as your CTO, PM, and senior developer assistant — tracking projects, analyzing conversations, scoring project health, and generating next steps.

## Run & Operate

- `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000` — run the FastAPI backend
- API docs: http://localhost:8000/docs (Swagger UI)
- Health check: GET /health

## Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.115
- **ORM**: SQLAlchemy 2.0 (sync)
- **DB**: PostgreSQL (Supabase-compatible)
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Validation**: Pydantic v2 + pydantic-settings

## Where things live

- `backend/app/main.py` — FastAPI app entry point, middleware, router registration
- `backend/app/core/config.py` — All settings via pydantic-settings (reads `.env`)
- `backend/app/core/security.py` — JWT creation/decode, bcrypt hash/verify
- `backend/app/core/rate_limiter.py` — In-memory rate limiter (10 req/min/IP)
- `backend/app/db/base.py` — SQLAlchemy declarative base + model imports
- `backend/app/db/session.py` — Engine, session factory, `init_db()`
- `backend/app/db/models/` — User, Project, Message, ProjectStatus ORM models
- `backend/app/db/schemas/` — Pydantic request/response schemas
- `backend/app/api/deps.py` — `get_current_user` JWT auth dependency
- `backend/app/api/routes/` — auth, projects, chat, status route handlers
- `backend/app/services/ai_service.py` — Rule-based AI analysis engine
- `backend/app/services/status_service.py` — Compute & persist project status
- `backend/app/services/project_service.py` — Project CRUD helpers

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check → `{"status":"ok"}` |
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

## Architecture decisions

- **Sync SQLAlchemy**: keeps connection model simple and avoids async complexity with psycopg2
- **Rule-based AI engine**: zero external API cost; analyzes message keywords for problems/progress/stuck points
- **JWT in Bearer header**: stateless auth, no session storage needed
- **In-memory rate limiter**: thread-safe with Lock; resets on restart (sufficient for single-instance)
- **Graceful DB startup**: `init_db()` failure is logged but doesn't crash the server

## Product

AI Teammate tracks your software projects and conversations, automatically detecting bugs/blockers vs. progress, calculating a 0–100 health score, identifying recurring stuck points, and generating a 5-step prioritized action plan — all from natural conversational messages.

## User preferences

- FastAPI + SQLAlchemy sync stack (strict requirement)
- No async DB operations
- Production-ready security (JWT, bcrypt, rate limiting, ORM-only queries)

## Gotchas

- `DATABASE_URL` must be set in `backend/.env` before the DB tables will be created
- The server starts successfully even without a DB connection (graceful failure)
- Rate limiter is in-memory — resets on process restart; for multi-instance deploy, swap with Redis
- `backend/.env` is gitignored; use `.env.example` as the template
- Run from the `backend/` directory so Python resolves `app.*` imports correctly

## Required env vars

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Postgres connection string |
| `SECRET_KEY` | Long random string for JWT signing |
| `ALGORITHM` | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL in minutes (default 10080 = 7 days) |
