import pytest
from httpx import ASGITransport, AsyncClient

from app.api import main as api_main


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
