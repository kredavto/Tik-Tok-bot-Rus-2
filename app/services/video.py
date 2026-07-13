import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

SUPPORTED_SUFFIXES = {".mp4", ".mov", ".webm"}


@dataclass(frozen=True)
class VideoInspection:
    is_valid: bool
    needs_transcode: bool
    path: Path
    duration_sec: float | None = None
    codec_name: str | None = None
    error: str | None = None


async def inspect_video(path: str) -> VideoInspection:
    video_path = Path(path)
    if not video_path.exists() or not video_path.is_file():
        return VideoInspection(False, False, video_path, error="file_not_found")
    if video_path.stat().st_size > settings.max_video_size_mb * 1024 * 1024:
        return VideoInspection(False, False, video_path, error="file_too_large")
    if video_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        return VideoInspection(False, False, video_path, error="unsupported_extension")
    if not _has_supported_signature(video_path):
        return VideoInspection(False, False, video_path, error="unsupported_container_signature")

    metadata = await _ffprobe(video_path)
    if not metadata:
        return VideoInspection(False, False, video_path, error="ffprobe_failed")

    duration = _extract_duration(metadata)
    if duration and duration > settings.max_video_duration_sec:
        return VideoInspection(
            False, False, video_path, duration_sec=duration, error="duration_too_long"
        )

    codec = _extract_video_codec(metadata)
    needs_transcode = video_path.suffix.lower() == ".webm"
    return VideoInspection(
        True, needs_transcode, video_path, duration_sec=duration, codec_name=codec
    )


async def prepare_video_for_tiktok(path: str) -> Path:
    inspection = await inspect_video(path)
    if not inspection.is_valid:
        raise ValueError(inspection.error or "invalid_video")
    if not inspection.needs_transcode:
        return inspection.path

    target = inspection.path.with_suffix(".mp4")
    if target.exists():
        return target

    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i",
        str(inspection.path),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(target),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise ValueError(f"ffmpeg_failed: {stderr.decode('utf-8', errors='ignore')[:200]}")
    return target


async def cleanup_temp_file(path: str) -> None:
    video_path = Path(path)
    for candidate in {video_path, video_path.with_suffix(".mp4")}:
        try:
            if candidate.exists() and candidate.is_file():
                candidate.unlink()
        except OSError:
            pass


def _has_supported_signature(path: Path) -> bool:
    header = path.read_bytes()[:16]
    suffix = path.suffix.lower()
    if suffix in {".mp4", ".mov"}:
        return len(header) >= 12 and header[4:8] == b"ftyp"
    if suffix == ".webm":
        return header.startswith(bytes.fromhex("1A45DFA3"))
    return False


async def _ffprobe(path: Path) -> dict | None:
    process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()
    if process.returncode != 0:
        return None
    return json.loads(stdout.decode("utf-8"))


def _extract_duration(metadata: dict) -> float | None:
    duration = metadata.get("format", {}).get("duration")
    return float(duration) if duration else None


def _extract_video_codec(metadata: dict) -> str | None:
    for stream in metadata.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream.get("codec_name")
    return None
