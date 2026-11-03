from app.core.config import settings


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "version": settings.APP_VERSION}


def test_root_points_to_docs(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["docs"] == "/docs"
    assert settings.APP_NAME in body["message"]


def test_openapi_lists_core_routes(client):
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]
    for path in (
        "/health",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/me",
        "/api/v1/projects/",
        "/api/v1/billing/plans",
        "/api/v1/dashboard/overview",
    ):
        assert path in paths, f"{path} missing from OpenAPI schema"


def test_billing_plans_are_public(client):
    res = client.get("/api/v1/billing/plans")
    assert res.status_code == 200
    plans = res.json()
    assert {p["id"] for p in plans} >= {"free", "pro"}
    for plan in plans:
        assert plan["daily_credits"] > 0
        assert plan["monthly_credits"] >= plan["daily_credits"]
        assert plan["price_inr"] >= 0


def test_me_requires_auth(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code in (401, 403)


def test_me_rejects_invalid_token(client):
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_projects_require_auth(client):
    res = client.get("/api/v1/projects/")
    assert res.status_code in (401, 403)


def test_register_validates_body(client):
    res = client.post("/api/v1/auth/register", json={"email": "not-an-email"})
    assert res.status_code == 422


def test_oversized_request_rejected(client):
    too_big = str(settings.MAX_REQUEST_SIZE + 1)
    res = client.post("/api/v1/auth/login", content=b"{}", headers={"Content-Length": too_big, "Content-Type": "application/json"})
    assert res.status_code == 413
