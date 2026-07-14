from hashlib import sha256
import hmac

import pytest

from app.services.tiktok import (
    TikTokApiError,
    TikTokClient,
    _chunk_plan,
    _truncate_utf16,
    _upload_chunk,
    build_oauth_url,
    validate_webhook_signature,
)


def test_tiktok_oauth_url_contains_official_scope(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "tiktok_client_key", "client")
    monkeypatch.setattr(
        settings, "tiktok_redirect_uri", "https://example.com/oauth/tiktok/callback"
    )

    url = build_oauth_url("state123")

    assert url.startswith("https://www.tiktok.com/v2/auth/authorize/")
    assert "video.publish" in url
    assert "state=state123" in url


def test_tiktok_webhook_signature_and_replay_window(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "tiktok_client_secret", "client-secret")
    raw_body = b'{"event":"post.publish.complete"}'
    timestamp = "1700000000"
    signed = timestamp.encode() + b"." + raw_body
    signature = hmac.new(b"client-secret", signed, sha256).hexdigest()
    header = f"t={timestamp},s={signature}"

    assert validate_webhook_signature(raw_body, header, now=1_700_000_100)
    assert not validate_webhook_signature(raw_body, header, now=1_700_000_301)
    assert not validate_webhook_signature(raw_body + b" ", header, now=1_700_000_100)


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (4_000_000, (4_000_000, 1)),
        (64_000_000, (64_000_000, 1)),
        (65_000_000, (10_000_000, 7)),
        (100_000_000, (10_000_000, 10)),
    ],
)
def test_tiktok_chunk_plan(size: int, expected: tuple[int, int]) -> None:
    assert _chunk_plan(size) == expected


def test_caption_is_limited_by_utf16_units() -> None:
    value = "a" * 2199 + "😀" + "tail"
    result = _truncate_utf16(value, 2200)

    assert len(result.encode("utf-16-le")) // 2 <= 2200
    assert result == "a" * 2199


@pytest.mark.asyncio
async def test_creator_info_is_parsed_from_official_response(monkeypatch) -> None:
    async def fake_post(path: str, payload: dict) -> dict:
        assert path == "/post/publish/creator_info/query/"
        assert payload == {}
        return {
            "data": {
                "creator_username": "creator",
                "creator_nickname": "Creator Name",
                "privacy_level_options": ["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS"],
                "comment_disabled": False,
                "duet_disabled": True,
                "stitch_disabled": False,
                "max_video_post_duration_sec": 180,
            }
        }

    client = TikTokClient("token")
    monkeypatch.setattr(client, "_post", fake_post)

    creator = await client.query_creator_info()

    assert creator.nickname == "Creator Name"
    assert creator.privacy_level_options == ("SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS")
    assert creator.duet_disabled is True
    assert creator.max_video_post_duration_sec == 180


class FakeUploadResponse:
    def __init__(self, status: int, body: str = "response") -> None:
        self.status = status
        self.body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def text(self) -> str:
        return self.body


class FakeUploadSession:
    def __init__(self, statuses: list[int]) -> None:
        self.statuses = statuses
        self.requests = 0

    def put(self, *_args, **_kwargs) -> FakeUploadResponse:
        self.requests += 1
        return FakeUploadResponse(self.statuses.pop(0))


@pytest.mark.asyncio
async def test_upload_chunk_retries_temporary_server_error(monkeypatch) -> None:
    delays: list[int] = []

    async def fake_sleep(seconds: int) -> None:
        delays.append(seconds)

    monkeypatch.setattr("app.services.tiktok.asyncio.sleep", fake_sleep)
    session = FakeUploadSession([500, 201])

    await _upload_chunk(
        session=session,  # type: ignore[arg-type]
        upload_url="https://upload.example.test/video",
        chunk=b"video",
        content_type="video/mp4",
        content_range="bytes 0-4/5",
        expected_status=201,
    )

    assert session.requests == 2
    assert delays == [1]


@pytest.mark.asyncio
async def test_upload_chunk_does_not_retry_client_error(monkeypatch) -> None:
    sleep = pytest.fail
    monkeypatch.setattr("app.services.tiktok.asyncio.sleep", sleep)
    session = FakeUploadSession([400])

    with pytest.raises(TikTokApiError, match="response"):
        await _upload_chunk(
            session=session,  # type: ignore[arg-type]
            upload_url="https://upload.example.test/video",
            chunk=b"video",
            content_type="video/mp4",
            content_range="bytes 0-4/5",
            expected_status=201,
        )

    assert session.requests == 1
