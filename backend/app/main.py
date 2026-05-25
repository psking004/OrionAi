from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.utils.logger import get_logger
from app.api.routes import auth, projects, chat, status as status_router
from app.api.routes import github as github_router
from app.api.routes import upload as upload_router
from app.api.routes import billing as billing_router
from app.api.routes import dashboard as dashboard_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.db.session import init_db
        init_db()
        logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    except Exception as exc:
        logger.error(f"DB init failed (non-fatal — set DATABASE_URL to enable): {exc}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered productivity platform — your AI CTO, PM, and senior dev teammate.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# allow_credentials=True requires explicit origins (not "*").
# When the caller passes "*" we disable credentials to keep browsers happy.
_origins = settings.CORS_ORIGINS
_allow_credentials = "*" not in _origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Request size guard ────────────────────────────────────────────────────────
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_REQUEST_SIZE:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,           prefix="/api/v1")
app.include_router(projects.router,       prefix="/api/v1")
app.include_router(chat.router,           prefix="/api/v1")
app.include_router(status_router.router,  prefix="/api/v1")
app.include_router(github_router.router,   prefix="/api/v1")
app.include_router(upload_router.router,   prefix="/api/v1")
app.include_router(billing_router.router,  prefix="/api/v1")
app.include_router(dashboard_router.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/", tags=["root"])
def root():
    return {"message": f"Welcome to {settings.APP_NAME} API", "docs": "/docs"}


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
