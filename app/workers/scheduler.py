import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import sys

from redis.asyncio import Redis

from app.core.config import settings, validate_runtime_settings
from app.core.logging import configure_logging
from app.core.redis import get_redis
from app.workers.tasks import (
    cleanup_retention,
    expire_subscriptions,
    reconcile_processing_uploads,
    refresh_expiring_tiktok_tokens,
)

logger = logging.getLogger(__name__)
HEARTBEAT_KEY = "scheduler:heartbeat"


@dataclass(frozen=True)
class PeriodicDispatch:
    name: str
    interval_seconds: int
    enqueue: Callable[[], object]


def periodic_dispatches() -> tuple[PeriodicDispatch, ...]:
    return (
        PeriodicDispatch(
            "expire_subscriptions",
            settings.subscription_sweep_seconds,
            expire_subscriptions.send,
        ),
        PeriodicDispatch(
            "refresh_tiktok_tokens",
            settings.token_refresh_sweep_seconds,
            refresh_expiring_tiktok_tokens.send,
        ),
        PeriodicDispatch(
            "cleanup_retention",
            settings.retention_sweep_seconds,
            cleanup_retention.send,
        ),
        PeriodicDispatch(
            "reconcile_processing_uploads",
            settings.status_reconcile_seconds,
            reconcile_processing_uploads.send,
        ),
    )


async def dispatch_once(redis: Redis, dispatches: Sequence[PeriodicDispatch]) -> list[str]:
    dispatched: list[str] = []
    for item in dispatches:
        claimed = await redis.set(
            f"scheduler:lease:{item.name}",
            datetime.now(UTC).isoformat(),
            ex=item.interval_seconds,
            nx=True,
        )
        if claimed:
            try:
                item.enqueue()
            except Exception:
                await redis.delete(f"scheduler:lease:{item.name}")
                raise
            dispatched.append(item.name)
    return dispatched


async def run_scheduler() -> None:
    validate_runtime_settings()
    redis = get_redis()
    heartbeat_ttl = max(60, settings.scheduler_tick_seconds * 6)
    try:
        while True:
            try:
                await redis.setex(
                    HEARTBEAT_KEY,
                    heartbeat_ttl,
                    datetime.now(UTC).isoformat(),
                )
                dispatched = await dispatch_once(redis, periodic_dispatches())
                if dispatched:
                    logger.info("Periodic tasks dispatched", extra={"tasks": dispatched})
            except Exception:
                logger.exception("Scheduler tick failed")
            await asyncio.sleep(settings.scheduler_tick_seconds)
    finally:
        await redis.aclose()


async def scheduler_is_healthy() -> bool:
    redis = get_redis()
    try:
        return bool(await redis.get(HEARTBEAT_KEY))
    finally:
        await redis.aclose()


def main() -> int:
    configure_logging()
    if "--healthcheck" in sys.argv:
        return 0 if asyncio.run(scheduler_is_healthy()) else 1
    asyncio.run(run_scheduler())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
