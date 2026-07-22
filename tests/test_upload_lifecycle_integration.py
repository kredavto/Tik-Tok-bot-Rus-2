import random

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.core.config import settings
from app.core.upload_status import UploadStatus
from app.db.models import UploadJobEvent
from app.db.session import (
    create_upload_job,
    get_or_create_user,
    init_db,
    session_scope,
    transition_upload_job,
    upsert_tiktok_account,
)


@pytest.mark.asyncio
async def test_upload_lifecycle_persists_every_status_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await init_db()
    if not settings.token_encryption_key:
        monkeypatch.setattr(
            settings,
            "token_encryption_key",
            Fernet.generate_key().decode("ascii"),
        )
    telegram_id = random.randint(700_000_000, 799_999_999)

    async with session_scope() as session:
        user = await get_or_create_user(session, telegram_id, "lifecycle_user")
        account = await upsert_tiktok_account(
            session=session,
            user_id=user.id,
            open_id=f"qa-open-id-{telegram_id}",
            display_name="QA Creator",
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_in=3600,
            scopes="user.info.basic,video.publish",
        )
        job = await create_upload_job(
            session=session,
            user_id=user.id,
            tiktok_account_id=account.id,
            telegram_file_id="telegram-file-id",
            local_path="/tmp/qa-video.mp4",
            caption="QA publication",
            privacy_level="SELF_ONLY",
            disable_comment=True,
            disable_duet=True,
            disable_stitch=True,
            brand_content_toggle=False,
            brand_organic_toggle=False,
        )
        job_id = job.id
        for status in (
            UploadStatus.VALIDATING,
            UploadStatus.PREPARING,
            UploadStatus.QUEUED,
            UploadStatus.UPLOADING,
            UploadStatus.PROCESSING,
            UploadStatus.PUBLISHED,
        ):
            await transition_upload_job(session, job, status, f"Moved to {status.value}")

    async with session_scope() as session:
        events = list(
            (
                await session.scalars(
                    select(UploadJobEvent)
                    .where(UploadJobEvent.upload_job_id == job_id)
                    .order_by(UploadJobEvent.created_at, UploadJobEvent.id)
                )
            ).all()
        )

    assert [event.status for event in events] == [status.value for status in UploadStatus][:-2]


def test_terminal_upload_status_cannot_be_reopened() -> None:
    from app.core.upload_status import validate_upload_transition

    with pytest.raises(ValueError, match="Invalid upload status transition"):
        validate_upload_transition(UploadStatus.PUBLISHED.value, UploadStatus.QUEUED)
