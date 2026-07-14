from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workers import tasks


@pytest.mark.asyncio
async def test_upload_worker_skips_job_when_lock_is_busy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    @asynccontextmanager
    async def busy_lock(_upload_id: str) -> AsyncIterator[bool]:
        yield False

    process_locked = AsyncMock()
    monkeypatch.setattr(tasks, "upload_job_lock", busy_lock)
    monkeypatch.setattr(tasks, "_process_upload_locked", process_locked)

    await tasks._process_upload("upload-id", "user-id")

    process_locked.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_worker_runs_once_after_lock_acquisition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    @asynccontextmanager
    async def acquired_lock(_upload_id: str) -> AsyncIterator[bool]:
        yield True

    process_locked = AsyncMock()
    monkeypatch.setattr(tasks, "upload_job_lock", acquired_lock)
    monkeypatch.setattr(tasks, "_process_upload_locked", process_locked)

    await tasks._process_upload("upload-id", "user-id")

    process_locked.assert_awaited_once()


@pytest.mark.asyncio
async def test_tiktok_acceptance_is_committed_before_local_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    upload = SimpleNamespace(tiktok_publish_id=None)
    user = SimpleNamespace()
    transition = AsyncMock()
    monkeypatch.setattr(tasks, "consume_daily_upload", AsyncMock(return_value=(True, 1, 2)))
    monkeypatch.setattr(tasks, "transition_upload_job", transition)

    await tasks._persist_tiktok_acceptance(session, upload, user, "publish-id")

    assert upload.tiktok_publish_id == "publish-id"
    transition.assert_awaited_once_with(
        session,
        upload,
        tasks.UploadStatus.PROCESSING,
        "TikTok is processing publication",
    )
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_tiktok_acceptance_is_not_committed_when_quota_cannot_be_consumed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    upload = SimpleNamespace(tiktok_publish_id=None)
    monkeypatch.setattr(tasks, "consume_daily_upload", AsyncMock(return_value=(False, 2, 2)))

    with pytest.raises(RuntimeError, match="Daily usage changed"):
        await tasks._persist_tiktok_acceptance(
            session,
            upload,
            SimpleNamespace(),
            "publish-id",
        )

    assert upload.tiktok_publish_id is None
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_local_failures_do_not_reclassify_tiktok_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = SimpleNamespace(setex=AsyncMock(side_effect=RuntimeError("redis unavailable")))
    cleanup = AsyncMock(side_effect=OSError("disk unavailable"))
    notify = AsyncMock()
    enqueue = MagicMock(side_effect=RuntimeError("broker unavailable"))
    monkeypatch.setattr(tasks, "cleanup_temp_file", cleanup)
    monkeypatch.setattr(tasks, "_notify", notify)
    monkeypatch.setattr(tasks.check_publish_status, "send_with_options", enqueue)

    await tasks._finish_accepted_upload(
        redis=redis,
        bot=None,
        upload_id="upload-id",
        user_id="user-id",
        telegram_id=123,
        local_path="/tmp/video.mp4",
    )

    enqueue.assert_called_once()
    notify.assert_awaited_once()
    cleanup.assert_awaited_once_with("/tmp/video.mp4")
