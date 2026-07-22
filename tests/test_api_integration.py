import pytest
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from app.api import main as api_main


class FakeRedis:
    async def incr(self, _key: str) -> int:
        return 1

    async def expire(self, _key: str, _seconds: int) -> bool:
        return True

    async def aclose(self) -> None:
        return None


@pytest.fixture(autouse=True)
def fake_rate_limit_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_main, "get_redis", FakeRedis)


@pytest.mark.asyncio
async def test_health_and_metrics_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    async def collect_metrics() -> dict[str, int]:
        return {"registrations_total": 3}

    monkeypatch.setattr(api_main, "_collect_dynamic_metrics", collect_metrics)
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/health")
        metrics = await client.get("/metrics")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert metrics.status_code == 200
    assert "tiktok_loader_http_requests_total" in metrics.text


@pytest.mark.asyncio
async def test_request_and_correlation_ids_are_propagated() -> None:
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/health",
            headers={"X-Request-ID": "req-qa", "X-Correlation-ID": "corr-qa"},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-qa"
    assert response.headers["X-Correlation-ID"] == "corr-qa"


@pytest.mark.asyncio
async def test_tiktok_webhook_rejects_invalid_signature_with_safe_error_contract() -> None:
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/webhooks/tiktok",
            content=b'{"event":"post.publish.complete"}',
            headers={"X-Request-ID": "req-webhook"},
        )

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "error": {"code": "TT_401", "message": "Invalid TikTok webhook signature"},
        "request_id": "req-webhook",
        "correlation_id": "req-webhook",
    }


@pytest.mark.asyncio
async def test_oauth_start_rejects_unknown_state(monkeypatch: pytest.MonkeyPatch) -> None:
    async def state_does_not_exist(_state: str) -> bool:
        return False

    monkeypatch.setattr(api_main, "oauth_state_exists", state_does_not_exist)
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/oauth/tiktok/start",
            params={"state": "a" * 32},
        )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_400"
    assert body["request_id"]


@pytest.mark.asyncio
async def test_validation_errors_use_catalog_code() -> None:
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/oauth/tiktok/start", params={"state": "short"})

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "VAL_422",
        "message": "Request validation failed",
    }


def test_openapi_contains_required_public_contracts() -> None:
    schema = api_main.app.openapi()
    required_paths = {
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/metrics",
        "/api/v1/oauth/tiktok/start",
        "/api/v1/oauth/tiktok/callback",
        "/api/v1/webhooks/telegram",
        "/api/v1/webhooks/tiktok",
        "/api/v1/payments/robokassa/result",
        "/api/v1/payments/robokassa/success",
        "/api/v1/payments/robokassa/fail",
    }

    assert required_paths <= schema["paths"].keys()


def test_rate_limit_uses_forwarded_client_from_private_proxy() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/ready",
            "headers": [(b"x-real-ip", b"203.0.113.10")],
            "client": ("172.19.0.5", 42000),
            "server": ("api", 8080),
            "scheme": "http",
            "query_string": b"",
        }
    )

    assert api_main._rate_limit_identity(request) == "203.0.113.10"


def test_rate_limit_ignores_forwarded_client_from_public_peer() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/ready",
            "headers": [(b"x-real-ip", b"1.1.1.1")],
            "client": ("8.8.8.8", 42000),
            "server": ("api", 8080),
            "scheme": "http",
            "query_string": b"",
        }
    )

    assert api_main._rate_limit_identity(request) == "8.8.8.8"


def test_robokassa_payment_method_alias_is_not_treated_as_currency() -> None:
    assert api_main._robokassa_output_currency_is_valid({"IncCurrLabel": "BankCard"})
    assert not api_main._robokassa_output_currency_is_valid({"OutCurrLabel": "USD"})
