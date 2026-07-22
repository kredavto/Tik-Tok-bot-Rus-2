from pathlib import Path

import pytest

from app.core.config import settings
from app.services import video


def write_mp4(path: Path) -> None:
    path.write_bytes(b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00")


def write_webm(path: Path) -> None:
    path.write_bytes(bytes.fromhex("1A45DFA3") + b"\x00" * 12)


@pytest.mark.asyncio
async def test_inspect_video_accepts_valid_mp4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "clip.mp4"
    write_mp4(source)

    async def ffprobe(_path: Path) -> dict:
        return {
            "format": {"duration": "12.5"},
            "streams": [{"codec_type": "video", "codec_name": "h264"}],
        }

    monkeypatch.setattr(video, "_ffprobe", ffprobe)
    result = await video.inspect_video(str(source))

    assert result.is_valid is True
    assert result.needs_transcode is False
    assert result.duration_sec == 12.5
    assert result.codec_name == "h264"


@pytest.mark.asyncio
async def test_inspect_video_rejects_signature_before_ffprobe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "not-video.mp4"
    source.write_text("plain text", encoding="utf-8")
    ffprobe = pytest.fail
    monkeypatch.setattr(video, "_ffprobe", ffprobe)

    result = await video.inspect_video(str(source))

    assert result.is_valid is False
    assert result.error == "unsupported_container_signature"


@pytest.mark.asyncio
async def test_inspect_video_rejects_excessive_duration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "long.mov"
    write_mp4(source)

    async def ffprobe(_path: Path) -> dict:
        return {"format": {"duration": str(settings.max_video_duration_sec + 1)}}

    monkeypatch.setattr(video, "_ffprobe", ffprobe)
    result = await video.inspect_video(str(source))

    assert result.is_valid is False
    assert result.error == "duration_too_long"


@pytest.mark.asyncio
async def test_prepare_webm_is_idempotent_when_target_exists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "clip.webm"
    target = tmp_path / "clip.mp4"
    write_webm(source)
    write_mp4(target)

    async def ffprobe(_path: Path) -> dict:
        return {"format": {"duration": "8"}, "streams": []}

    monkeypatch.setattr(video, "_ffprobe", ffprobe)
    result = await video.prepare_video_for_tiktok(str(source))

    assert result == target


@pytest.mark.asyncio
async def test_cleanup_removes_source_and_transcoded_copy(tmp_path: Path) -> None:
    source = tmp_path / "clip.webm"
    target = tmp_path / "clip.mp4"
    write_webm(source)
    write_mp4(target)

    await video.cleanup_temp_file(str(source))

    assert not source.exists()
    assert not target.exists()
