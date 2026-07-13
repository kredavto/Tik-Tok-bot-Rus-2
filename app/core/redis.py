import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from app.core.config import settings
from app.core.upload_status import UploadStatus


def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def create_oauth_state(user_id: str) -> str:
    state = secrets.token_urlsafe(32)
    redis = get_redis()
    try:
        await redis.setex(f"oauth_state:{state}", 600, user_id)
    finally:
        await redis.aclose()
    return state


async def pop_oauth_state(state: str) -> str | None:
    redis = get_redis()
    try:
        key = f"oauth_state:{state}"
        user_id = await redis.get(key)
        if user_id:
            await redis.delete(key)
        return user_id
    finally:
        await redis.aclose()


async def oauth_state_exists(state: str) -> bool:
    redis = get_redis()
    try:
        return bool(await redis.exists(f"oauth_state:{state}"))
    finally:
        await redis.aclose()


async def enqueue_upload(upload_id: str, user_id: str) -> None:
    from app.workers.tasks import process_upload

    redis = get_redis()
    try:
        await redis.setex(f"upload:{upload_id}:status", 86400, UploadStatus.QUEUED.value)
        process_upload.send(upload_id, user_id)
    finally:
        await redis.aclose()


@asynccontextmanager
async def user_limit_lock(user_id: str) -> AsyncIterator[None]:
    redis = get_redis()
    lock = redis.lock(f"lock:daily_limit:{user_id}", timeout=900, blocking_timeout=30)
    try:
        async with lock:
            yield
    finally:
        await redis.aclose()


@asynccontextmanager
async def upload_job_lock(upload_id: str) -> AsyncIterator[bool]:
    redis = get_redis()
    lock = redis.lock(f"lock:upload_job:{upload_id}", timeout=900, blocking_timeout=0)
    acquired = await lock.acquire()
    try:
        yield acquired
    finally:
        if acquired:
            await lock.release()
        await redis.aclose()
