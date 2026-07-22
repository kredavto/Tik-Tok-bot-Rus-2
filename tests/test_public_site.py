from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

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
@pytest.mark.parametrize(
    ("path", "title"),
    [
        ("/", "Tik_Tok_Loader"),
        ("/legal/terms", "Terms of Service"),
        ("/legal/privacy", "Privacy Policy"),
    ],
)
async def test_public_pages_are_available_with_security_headers(path: str, title: str) -> None:
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)

    assert response.status_code == 200
    assert title in response.text
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_public_icon_meets_tiktok_portal_requirements() -> None:
    icon_path = Path(api_main.PUBLIC_DIR) / "static" / "app-icon.png"
    width = int.from_bytes(icon_path.read_bytes()[16:20], "big")
    height = int.from_bytes(icon_path.read_bytes()[20:24], "big")

    assert icon_path.stat().st_size <= 5 * 1024 * 1024
    assert (width, height) == (1024, 1024)

    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/assets/app-icon.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_tiktok_verification_file_is_served_verbatim() -> None:
    verification_path = Path(api_main.PUBLIC_DIR) / api_main.TIKTOK_VERIFICATION_FILENAME
    expected_content = verification_path.read_bytes()

    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(api_main.TIKTOK_VERIFICATION_URL_PATH)

    assert response.status_code == 200
    assert response.content == expected_content
    assert response.headers["content-type"].startswith("text/plain")
    assert response.headers["x-content-type-options"] == "nosniff"
