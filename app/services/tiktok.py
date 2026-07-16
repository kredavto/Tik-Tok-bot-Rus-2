import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import hmac
from pathlib import Path
from urllib.parse import urlencode

import aiofiles  # type: ignore
import aiohttp

from app.core.config import settings


class TikTokPublishingDisabled(RuntimeError):
    pass


class TikTokApiError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int | None = None) -> None:
        self.code = code
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class TikTokTokenResponse:
    open_id: str
    access_token: str
    refresh_token: str | None
    expires_in: int | None
    scope: str | None


@dataclass(frozen=True)
class TikTokUserInfo:
    open_id: str
    display_name: str | None


@dataclass(frozen=True)
class TikTokPostResult:
    publish_id: str
    status: str


@dataclass(frozen=True)
class TikTokCreatorInfo:
    username: str
    nickname: str
    privacy_level_options: tuple[str, ...]
    comment_disabled: bool
    duet_disabled: bool
    stitch_disabled: bool
    max_video_post_duration_sec: int


@dataclass(frozen=True)
class TikTokPostStatus:
    status: str
    fail_reason: str | None = None


@dataclass(frozen=True)
class TikTokPostOptions:
    privacy_level: str
    disable_comment: bool
    disable_duet: bool
    disable_stitch: bool
    brand_content_toggle: bool = False
    brand_organic_toggle: bool = False


def build_oauth_url(state: str) -> str:
    params = {
        "client_key": settings.tiktok_client_key,
        "scope": "user.info.basic,video.publish",
        "response_type": "code",
        "redirect_uri": settings.tiktok_redirect_uri,
        "state": state,
    }
    return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"


class TikTokClient:
    api_base = "https://open.tiktokapis.com/v2"
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token

    async def exchange_code(self, code: str) -> TikTokTokenResponse:
        payload = {
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.tiktok_redirect_uri,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=payload) as response:
                data = await response.json()
                if response.status >= 400:
                    raise TikTokApiError(
                        str(data.get("error", "oauth_error")),
                        str(data),
                        status_code=response.status,
                    )

        return TikTokTokenResponse(
            open_id=data["open_id"],
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope"),
        )

    async def refresh_access_token(self, refresh_token: str) -> TikTokTokenResponse:
        payload = {
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=payload) as response:
                data = await response.json()
                if response.status >= 400:
                    raise TikTokApiError(
                        str(data.get("error", "oauth_refresh_error")),
                        str(data),
                        status_code=response.status,
                    )

        return TikTokTokenResponse(
            open_id=data["open_id"],
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_in=data.get("expires_in"),
            scope=data.get("scope"),
        )

    async def get_user_info(self) -> TikTokUserInfo:
        data = await self._get("/user/info/?fields=open_id,display_name")
        user = data["data"]["user"]
        return TikTokUserInfo(open_id=user["open_id"], display_name=user.get("display_name"))

    async def query_creator_info(self) -> TikTokCreatorInfo:
        data = await self._post("/post/publish/creator_info/query/", {})
        creator = data["data"]
        return TikTokCreatorInfo(
            username=str(creator.get("creator_username", "")),
            nickname=str(creator.get("creator_nickname", "")),
            privacy_level_options=tuple(creator.get("privacy_level_options") or ()),
            comment_disabled=bool(creator.get("comment_disabled", False)),
            duet_disabled=bool(creator.get("duet_disabled", False)),
            stitch_disabled=bool(creator.get("stitch_disabled", False)),
            max_video_post_duration_sec=int(creator.get("max_video_post_duration_sec") or 0),
        )

    async def publish_video(
        self,
        video_path: Path,
        title: str,
        options: TikTokPostOptions,
    ) -> TikTokPostResult:
        if not settings.tiktok_publish_enabled:
            raise TikTokPublishingDisabled(
                "TikTok publishing is disabled until official API approval."
            )
        if not self.access_token:
            raise TikTokApiError("auth_required", "TikTok access token is required.")
        if options.brand_content_toggle and options.privacy_level == "SELF_ONLY":
            raise TikTokApiError(
                "invalid_post_options",
                "Branded content cannot use the SELF_ONLY privacy level.",
            )

        size = video_path.stat().st_size
        chunk_size, total_chunk_count = _chunk_plan(size)
        init_payload = {
            "post_info": {
                "title": _truncate_utf16(title, 2200),
                "privacy_level": options.privacy_level,
                "disable_duet": options.disable_duet,
                "disable_comment": options.disable_comment,
                "disable_stitch": options.disable_stitch,
                "brand_content_toggle": options.brand_content_toggle,
                "brand_organic_toggle": options.brand_organic_toggle,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count,
            },
        }
        data = await self._post("/post/publish/video/init/", init_payload)
        upload_url = data["data"]["upload_url"]
        publish_id = data["data"]["publish_id"]

        content_type = {
            ".mov": "video/quicktime",
            ".webm": "video/webm",
        }.get(video_path.suffix.lower(), "video/mp4")
        async with (
            aiohttp.ClientSession() as session,
            aiofiles.open(video_path, "rb") as video_file,
        ):
            offset = 0
            for chunk_index in range(total_chunk_count):
                is_last = chunk_index == total_chunk_count - 1
                bytes_to_read = size - offset if is_last else chunk_size
                chunk = await video_file.read(bytes_to_read)
                if not chunk:
                    raise TikTokApiError("upload_failed", "Video chunk could not be read.")
                last_byte = offset + len(chunk) - 1
                await _upload_chunk(
                    session=session,
                    upload_url=upload_url,
                    chunk=chunk,
                    content_type=content_type,
                    content_range=f"bytes {offset}-{last_byte}/{size}",
                    expected_status=201 if is_last else 206,
                )
                offset = last_byte + 1

        return TikTokPostResult(publish_id=publish_id, status="processing")

    async def get_post_status(self, publish_id: str) -> TikTokPostStatus:
        data = await self._post("/post/publish/status/fetch/", {"publish_id": publish_id})
        status = data["data"]
        return TikTokPostStatus(
            status=str(status.get("status", "UNKNOWN")),
            fail_reason=status.get("fail_reason"),
        )

    async def _get(self, path: str) -> dict:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{self.api_base}{path}") as response:
                return await self._parse_response(response)

    async def _post(self, path: str, payload: dict) -> dict:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f"{self.api_base}{path}", json=payload) as response:
                return await self._parse_response(response)

    async def _parse_response(self, response: aiohttp.ClientResponse) -> dict:
        data = await response.json()
        error = data.get("error") or {}
        code = error.get("code")
        if response.status >= 400 or code not in (None, "ok"):
            raise TikTokApiError(
                str(code or response.status),
                error.get("message") or str(data),
                status_code=response.status,
            )
        return data


def token_is_expired(expires_at: datetime | None) -> bool:
    return bool(expires_at and expires_at <= datetime.now(UTC))


def _chunk_plan(size: int) -> tuple[int, int]:
    if size <= 0:
        raise ValueError("Video file is empty.")
    if size <= 64_000_000:
        return size, 1
    chunk_size = 10_000_000
    return chunk_size, (size + chunk_size - 1) // chunk_size


async def _upload_chunk(
    *,
    session: aiohttp.ClientSession,
    upload_url: str,
    chunk: bytes,
    content_type: str,
    content_range: str,
    expected_status: int,
) -> None:
    for attempt in range(3):
        async with session.put(
            upload_url,
            data=chunk,
            headers={
                "Content-Type": content_type,
                "Content-Length": str(len(chunk)),
                "Content-Range": content_range,
            },
        ) as response:
            if response.status == expected_status:
                return
            body = await response.text()
            if response.status < 500 or attempt == 2:
                raise TikTokApiError("upload_failed", body)
        await asyncio.sleep(2**attempt)


def _truncate_utf16(value: str, max_units: int) -> str:
    encoded = value.encode("utf-16-le")
    if len(encoded) <= max_units * 2:
        return value
    truncated = encoded[: max_units * 2]
    while truncated:
        try:
            return truncated.decode("utf-16-le")
        except UnicodeDecodeError:
            truncated = truncated[:-2]
    return ""


def validate_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    *,
    now: int | None = None,
    tolerance_seconds: int = 300,
) -> bool:
    values: dict[str, str] = {}
    for part in signature_header.split(","):
        key, separator, value = part.strip().partition("=")
        if separator:
            values[key] = value

    timestamp = values.get("t")
    signature = values.get("s")
    if not timestamp or not signature or not timestamp.isdigit():
        return False

    current_time = int(datetime.now(UTC).timestamp()) if now is None else now
    if abs(current_time - int(timestamp)) > tolerance_seconds:
        return False

    secret = settings.tiktok_client_secret
    if not secret:
        return False
    signed_payload = timestamp.encode("ascii") + b"." + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
