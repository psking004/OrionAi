import time
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException, status
from app.core.config import settings

_store: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def rate_limit(request: Request) -> None:
    ip = (request.client.host if request.client else None) or "unknown"
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW
    limit = settings.RATE_LIMIT_REQUESTS

    with _lock:
        _store[ip] = [t for t in _store[ip] if now - t < window]
        if len(_store[ip]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {limit} requests per {window}s.",
            )
        _store[ip].append(now)
