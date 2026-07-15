from pathlib import Path
import re
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.api import main as api_main
from app.api.admin import upload_job_is_retryable
from app.core.upload_status import UploadStatus


class FakeRedis:
    async def incr(self, _: str) -> int:
        return 1

    async def expire(self, _: str, __: int) -> None:
        return None

    async def aclose(self) -> None:
        return None


def upload_job(error: str | None, publish_id: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        status=UploadStatus.FAILED.value,
        error_message=error,
        tiktok_publish_id=publish_id,
    )


def test_only_transient_unaccepted_uploads_can_be_retried() -> None:
    assert upload_job_is_retryable(upload_job("Temporary network timeout"))  # type: ignore[arg-type]
    assert not upload_job_is_retryable(upload_job("TikTok authorization failed"))  # type: ignore[arg-type]
    assert not upload_job_is_retryable(  # type: ignore[arg-type]
        upload_job("Temporary network timeout", "publish-123")
    )


def test_admin_routes_are_available_under_versioned_api() -> None:
    paths = set(api_main.app.openapi()["paths"])
    assert "/api/v1/admin/dashboard" in paths
    assert "/api/v1/admin/users/{user_id}" in paths
    assert "/api/v1/admin/upload-jobs/{job_id}/retry" in paths
    assert "/api/v1/admin/audit-actions" in paths
    assert "/api/v1/admin/payments/robokassa/orders" in paths
    assert "/api/v1/admin/payments/{payment_id}/refund-stars" in paths


@pytest.mark.asyncio
async def test_admin_ui_is_served_with_security_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_main, "get_redis", lambda: FakeRedis())
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/admin-ui/")

    assert response.status_code == 200
    assert "Tik_Tok_Loader Admin" in response.text
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_admin_ui_assets_do_not_contain_embedded_credentials() -> None:
    asset_dir = Path(api_main.ADMIN_UI_DIR)
    source = "\n".join(path.read_text() for path in asset_dir.glob("*.*"))
    assert not re.search(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b", source)
    assert "sessionStorage" not in source
    assert "localStorage" not in source
