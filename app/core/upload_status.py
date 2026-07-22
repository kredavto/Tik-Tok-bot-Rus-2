from enum import StrEnum


class UploadStatus(StrEnum):
    NEW = "NEW"
    VALIDATING = "VALIDATING"
    PREPARING = "PREPARING"
    QUEUED = "QUEUED"
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


RETRYABLE_UPLOAD_STATUSES = {
    UploadStatus.NEW,
    UploadStatus.VALIDATING,
    UploadStatus.PREPARING,
    UploadStatus.QUEUED,
    UploadStatus.UPLOADING,
}


ALLOWED_UPLOAD_TRANSITIONS: dict[UploadStatus, frozenset[UploadStatus]] = {
    UploadStatus.NEW: frozenset(
        {UploadStatus.VALIDATING, UploadStatus.FAILED, UploadStatus.CANCELLED}
    ),
    UploadStatus.VALIDATING: frozenset(
        {UploadStatus.PREPARING, UploadStatus.FAILED, UploadStatus.CANCELLED}
    ),
    UploadStatus.PREPARING: frozenset(
        {UploadStatus.QUEUED, UploadStatus.FAILED, UploadStatus.CANCELLED}
    ),
    UploadStatus.QUEUED: frozenset(
        {UploadStatus.UPLOADING, UploadStatus.FAILED, UploadStatus.CANCELLED}
    ),
    UploadStatus.UPLOADING: frozenset(
        {UploadStatus.PROCESSING, UploadStatus.FAILED, UploadStatus.CANCELLED}
    ),
    UploadStatus.PROCESSING: frozenset(
        {UploadStatus.PUBLISHED, UploadStatus.FAILED, UploadStatus.CANCELLED}
    ),
    UploadStatus.PUBLISHED: frozenset(),
    UploadStatus.FAILED: frozenset(),
    UploadStatus.CANCELLED: frozenset(),
}


def validate_upload_transition(current: str, target: UploadStatus) -> None:
    try:
        current_status = UploadStatus(current)
    except ValueError as exc:
        raise ValueError(f"Unknown upload status: {current}") from exc
    if target not in ALLOWED_UPLOAD_TRANSITIONS[current_status]:
        raise ValueError(f"Invalid upload status transition: {current_status} -> {target}")
