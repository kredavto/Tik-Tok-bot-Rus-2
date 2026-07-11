from app.services.tiktok import build_oauth_url


def test_tiktok_oauth_url_contains_official_scope(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "tiktok_client_key", "client")
    monkeypatch.setattr(settings, "tiktok_redirect_uri", "https://example.com/oauth/tiktok/callback")

    url = build_oauth_url("state123")

    assert url.startswith("https://www.tiktok.com/v2/auth/authorize/")
    assert "video.publish" in url
    assert "state=state123" in url

