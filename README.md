# OrionOS

AI engineering operating system: a FastAPI backend (`backend/`), an Express
API gateway (`artifacts/api-server`) and a React/Vite dashboard
(`artifacts/dashboard`) in one pnpm workspace. See `replit.md` for the
architecture and API reference.

## Requirements

- Node.js 20+ and pnpm 10+ (`corepack enable` or `npm i -g pnpm`)
- Python 3.11+ and [uv](https://docs.astral.sh/uv/) (or pip)
- PostgreSQL (optional to boot; needed for auth/projects data)

## Setup

```bash
pnpm install                      # JS workspace
uv sync                           # Python backend deps (or: pip install -r backend/requirements.txt)
cp backend/.env.example backend/.env   # set DATABASE_URL and SECRET_KEY
cp .env.example .env              # optional; all Node values have defaults
```

## Development

Run each in its own terminal:

```bash
RELOAD=1 pnpm dev:backend   # FastAPI on :8000   (python main.py also works)
pnpm dev:api                # Express gateway on :8080, proxies to FastAPI
pnpm dev:web                # Dashboard on :5173, proxies /api to :8080
```

Open http://localhost:5173. FastAPI docs: http://localhost:8000/docs.

## Production

```bash
pnpm install --frozen-lockfile
pnpm build                  # typecheck + build every package
uv sync --frozen

PORT=8000 python main.py    # FastAPI backend (or: uv run main.py)
PORT=8080 pnpm start        # api-server (dist/index.mjs)
```

The dashboard builds to static files in `artifacts/dashboard/dist/public`;
serve them from any static host or CDN and route `/api` to the api-server
(`pnpm start:web` gives a quick preview server).

## Environment variables

Backend (`backend/.env`): `DATABASE_URL`, `SECRET_KEY` (required in production),
`ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`, `RATE_LIMIT_REQUESTS`,
`RATE_LIMIT_WINDOW`, `DEBUG`, `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`,
`STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID`, `STRIPE_TEAM_PRICE_ID` (optional).

Node services: `PORT`, `BASE_PATH`, `FASTAPI_URL`, `FASTAPI_TIMEOUT_MS`, `API_PROXY_TARGET`, `NODE_ENV`
(all optional, defaults in `.env.example`). Backend launcher: `HOST`, `PORT`, `RELOAD`.

On Replit everything above is injected automatically and `.replit` still works.
