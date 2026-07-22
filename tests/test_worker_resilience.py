from collections.abc import AsyncIterator
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.workers import tasks


def test_worker_threads_share_one_persistent_event_loop() -> None:
    async def identify_loop() -> int:
        await asyncio.sleep(0.01)
        return id(asyncio.get_running_loop())

    with ThreadPoolExecutor(max_workers=4) as executor:
        loop_ids = list(
            executor.map(
                lambda _: tasks._run_worker_coroutine(identify_loop()),
                range(8),
            )
        )

    assert len(set(loop_ids)) == 1


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
    upload = SimpleNamespace(tiktok_publish_id=None, usage_date=None)
    user = SimpleNamespace()
    transition = AsyncMock()
    record_accepted = AsyncMock(return_value=3)
    monkeypatch.setattr(tasks, "record_accepted_upload", record_accepted)
    monkeypatch.setattr(tasks, "transition_upload_job", transition)

    await tasks._persist_tiktok_acceptance(session, upload, user, "publish-id")

    assert upload.tiktok_publish_id == "publish-id"
    record_accepted.assert_awaited_once_with(session, user, upload.usage_date)
    transition.assert_awaited_once_with(
        session,
        upload,
        tasks.UploadStatus.PROCESSING,
        "TikTok is processing publication",
    )
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_tiktok_acceptance_is_recorded_after_plan_limit_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock()
    upload = SimpleNamespace(tiktok_publish_id=None, usage_date=None)
    record_accepted = AsyncMock(return_value=3)
    transition = AsyncMock()
    monkeypatch.setattr(tasks, "record_accepted_upload", record_accepted)
    monkeypatch.setattr(tasks, "transition_upload_job", transition)

    await tasks._persist_tiktok_acceptance(
        session,
        upload,
        SimpleNamespace(),
        "publish-id",
    )

    assert upload.tiktok_publish_id == "publish-id"
    record_accepted.assert_awaited_once()
    session.commit.assert_awaited_once()


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


@pytest.mark.asyncio
async def test_rejected_upload_cleans_temporary_video(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cleanup = AsyncMock()
    monkeypatch.setattr(tasks, "cleanup_temp_file", cleanup)

    await tasks._cleanup_unaccepted_upload("/tmp/rejected.mp4", accepted=False)
    await tasks._cleanup_unaccepted_upload("/tmp/accepted.mp4", accepted=True)

    cleanup.assert_awaited_once_with("/tmp/rejected.mp4")


def test_unaudited_tiktok_error_has_actionable_user_message() -> None:
    reason = tasks._tiktok_upload_error_reason("unaudited_client_can_only_post_to_private_accounts")

    assert "аккаунт должен быть приватным" in reason


def test_tiktok_internal_processing_error_is_reported_as_temporary() -> None:
    reason = tasks._tiktok_processing_error_reason("internal")

    assert "временная ошибка на стороне TikTok" in reason
    assert "повторите публикацию позже" in reason
    assert "Суточная попытка возвращена" in reason


def test_unknown_tiktok_processing_error_keeps_generic_message() -> None:
    reason = tasks._tiktok_processing_error_reason("unknown_reason")

    assert reason == "TikTok отклонил публикацию; суточная попытка возвращена"


@pytest.mark.asyncio
async def test_processing_reconciliation_requeues_accepted_uploads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [("upload-1", "user-1"), ("upload-2", "user-2")]
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(all=lambda: rows)))

    @asynccontextmanager
    async def fake_session_scope() -> AsyncIterator[object]:
        yield session

    enqueue = MagicMock()
    monkeypatch.setattr(tasks, "session_scope", fake_session_scope)
    monkeypatch.setattr(tasks.check_publish_status, "send", enqueue)

    count = await tasks._reconcile_processing_uploads()

    assert count == 2
    assert enqueue.call_args_list == [
        call("upload-1", "user-1", 0),
        call("upload-2", "user-2", 0),
    ]
