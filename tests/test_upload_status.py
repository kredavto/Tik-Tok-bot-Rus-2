import pytest

from app.core.upload_status import UploadStatus, validate_upload_transition


def test_upload_status_happy_path() -> None:
    validate_upload_transition(UploadStatus.NEW.value, UploadStatus.VALIDATING)
    validate_upload_transition(UploadStatus.PROCESSING.value, UploadStatus.PUBLISHED)


def test_upload_status_rejects_terminal_transition() -> None:
    with pytest.raises(ValueError, match="Invalid upload status transition"):
        validate_upload_transition(UploadStatus.PUBLISHED.value, UploadStatus.UPLOADING)
