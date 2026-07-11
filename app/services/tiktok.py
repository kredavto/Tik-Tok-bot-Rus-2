from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

import aiohttp

from app.core.config import settings


class TikTokPublishingDisabled(RuntimeError):
    pass


class TikTokApiError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
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
                    raise TikTokApiError(str(data.get("error", "oauth_error")), str(data))

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
                    raise TikTokApiError(str(data.get("error", "oauth_refresh_error")), str(data))

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

    async def publish_video(self, video_path: Path, title: str) -> TikTokPostResult:
        if not settings.tiktok_publish_enabled:
            raise TikTokPublishingDisabled("TikTok publishing is disabled until official API approval.")
        if not self.access_token:
            raise TikTokApiError("auth_required", "TikTok access token is required.")

        size = video_path.stat().st_size
        init_payload = {
            "post_info": {
                "title": title[:2200],
                "privacy_level": "SELF_ONLY",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": size,
                "total_chunk_count": 1,
            },
        }
        data = await self._post("/post/publish/video/init/", init_payload)
        upload_url = data["data"]["upload_url"]
        publish_id = data["data"]["publish_id"]

        async with aiohttp.ClientSession() as session:
            with video_path.open("rb") as video_file:
                async with session.put(
                    upload_url,
                    data=video_file,
                    headers={"Content-Range": f"bytes 0-{size - 1}/{size}"},
                ) as response:
                    if response.status >= 400:
                        raise TikTokApiError("upload_failed", await response.text())

        return TikTokPostResult(publish_id=publish_id, status="processing")

    async def get_post_status(self, publish_id: str) -> str:
        data = await self._post("/post/publish/status/fetch/", {"publish_id": publish_id})
        return data["data"].get("status", "unknown")

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
            raise TikTokApiError(str(code or response.status), error.get("message") or str(data))
        return data


def token_is_expired(expires_at: datetime | None) -> bool:
    return bool(expires_at and expires_at <= datetime.now(UTC))
