from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

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
