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
