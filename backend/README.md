# AI Teammate — Backend API

FastAPI backend for the **AI Teammate for Solo Developers** platform.  
Acts as your AI CTO, PM, and senior engineer — tracking projects, detecting problems, scoring health, and generating next steps.

---

## Quick Start

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — set DATABASE_URL and SECRET_KEY at minimum
```

### 3. Run
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive docs: http://localhost:8000/docs

---

## Deployment

### Replit
Set these secrets in the Replit Secrets panel:
- `DATABASE_URL` — your Postgres connection string
- `SECRET_KEY` — a long random string

Run command (already configured):
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Render / Railway
1. Set the same environment variables above in the dashboard
2. Set the start command to:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
3. Use a Supabase or managed Postgres for `DATABASE_URL`

---

## API Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/api/v1/auth/register` | No | Create account → returns JWT |
| POST | `/api/v1/auth/login` | No | Login → returns JWT |
| GET | `/api/v1/auth/me` | Yes | Current user |
| POST | `/api/v1/projects/` | Yes | Create project |
| GET | `/api/v1/projects/` | Yes | List your projects |
| GET | `/api/v1/projects/{id}` | Yes | Get one project |
| PATCH | `/api/v1/projects/{id}` | Yes | Update project |
| DELETE | `/api/v1/projects/{id}` | Yes | Delete project |
| POST | `/api/v1/projects/{id}/messages` | Yes | Add message to chat |
| GET | `/api/v1/projects/{id}/messages` | Yes | Get last 10 messages |
| POST | `/api/v1/projects/{id}/status` | Yes | Analyze & get project health |
| POST | `/api/v1/projects/{id}/next-steps` | Yes | Get prioritized roadmap |

All protected routes require: `Authorization: Bearer <token>`

---

## AI Teammate Logic

The engine analyzes your project's chat history to:

- **Detect problems**: keywords like `error`, `bug`, `failed`, `crash`, `broken`, `stuck`, `can't`
- **Detect progress**: keywords like `done`, `fixed`, `completed`, `deployed`, `shipped`
- **Identify stuck points**: topics repeated 2+ times across messages
- **Calculate health score**: 0–100 based on problem/progress ratio
- **Generate next steps**: 5 actionable tasks prioritized by severity
- **Detect missing features**: auth, testing, CI/CD, monitoring, etc.

### Health score legend
| Score | Label |
|-------|-------|
| 80–100 | `on_track` |
| 55–79 | `needs_attention` |
| 30–54 | `at_risk` |
| 0–29 | `critical` |

---

## Security
- Passwords hashed with bcrypt (passlib)
- JWT tokens signed with HS256
- Rate limiting: 10 req/min per IP
- SQL injection impossible via SQLAlchemy ORM
- Input validated with Pydantic v2
- Request body capped at 1 MB
- No secrets in code — all via environment variables

---

## Project Structure
```
backend/
├── app/
│   ├── main.py               # FastAPI app entry point
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   ├── security.py       # JWT + bcrypt
│   │   └── rate_limiter.py   # In-memory rate limiting
│   ├── db/
│   │   ├── base.py           # SQLAlchemy Base + model imports
│   │   ├── session.py        # Engine + session factory
│   │   ├── models/           # ORM models
│   │   └── schemas/          # Pydantic request/response schemas
│   ├── api/
│   │   ├── deps.py           # Auth dependency
│   │   └── routes/           # Route handlers
│   ├── services/
│   │   ├── ai_service.py     # AI analysis engine
│   │   ├── project_service.py
│   │   └── status_service.py
│   └── utils/
│       └── logger.py
├── requirements.txt
├── .env.example
├── replit.nix
└── README.md
```
