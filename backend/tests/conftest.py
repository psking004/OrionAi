import os

# Tests never touch a real database or Stripe: the routes covered here either
# don't use the DB or fail auth before any query runs.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/orionos_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.pop("STRIPE_SECRET_KEY", None)

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    # Not used as a context manager, so the startup hook (init_db) doesn't try to reach Postgres.
    return TestClient(app)
