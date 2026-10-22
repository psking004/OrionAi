"""Start the OrionOS FastAPI backend.

Usage:
    python main.py            # or: uv run main.py

Reads HOST (default 0.0.0.0), PORT (default 8000) and RELOAD (set to 1 for
auto-reload in development) from the environment. App settings such as
DATABASE_URL and SECRET_KEY are read from the environment or backend/.env.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"


def main() -> None:
    import uvicorn

    # Run from backend/ so `app.*` imports resolve and backend/.env is picked up.
    os.chdir(BACKEND_DIR)
    sys.path.insert(0, str(BACKEND_DIR))

    uvicorn.run(
        "app.main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("RELOAD", "").lower() in {"1", "true", "yes"},
    )


if __name__ == "__main__":
    main()
