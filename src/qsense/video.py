"""Video processing — direct passthrough and frame extraction modes."""

from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
from pathlib import Path

from ._util import abort as _abort
from .audio import AudioContentPart, prepare_audio
from .image import ImageContentPart, prepare_images

SUPPORTED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}

EXTENSION_TO_MIME: dict[str, str] = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
}

DIRECT_MAX_BYTES = 20 * 1024 * 1024  # 20 MB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        _abort("ffmpeg is required for video processing. See https://ffmpeg.org/download.html")
    return path


def _validate_video(path: Path) -> None:
    if not path.exists():
        _abort(f"Video file not found: {path}")
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        _abort(f"Unsupported video type: {path}")


def _run_ffmpeg(args: list[str]) -> None:
    """Run ffmpeg, abort on failure."""
    try:
        subprocess.run(
            args,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace").strip()
        _abort(f"ffmpeg failed: {stderr[:300]}")


def _has_audio_stream(ffmpeg: str, video_path: Path) -> bool:
    """Check if video file contains an audio stream."""
    try:
        result = subprocess.run(
            [ffmpeg, "-i", str(video_path), "-hide_banner"],
            capture_output=True,
            text=True,
        )
        # ffmpeg -i always exits non-zero, but prints stream info to stderr
        return "Audio:" in result.stderr
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Direct mode — encode whole video as data URL
# ---------------------------------------------------------------------------

def encode_video_direct(source: str) -> dict:
    """Encode a video as a data-URL content part (``image_url`` field).

    Used when the API proxy supports direct video passthrough.
    """
    if source.startswith(("http://", "https://")):
        return {"type": "image_url", "image_url": {"url": source}}

    path = Path(source).resolve()
    _validate_video(path)

    size = path.stat().st_size
    if size > DIRECT_MAX_BYTES:
        mb = size / 1024 / 1024
        _abort(f"Video too large for direct mode ({mb:.1f} MB, max {DIRECT_MAX_BYTES // 1024 // 1024} MB). "
               f"Use --video-extract for frame extraction.")

    mime = EXTENSION_TO_MIME[path.suffix.lower()]
    encoded = base64.b64encode(path.read_bytes()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}


# ---------------------------------------------------------------------------
# Extract mode — ffmpeg frames + audio
# ---------------------------------------------------------------------------

def extract_frames_and_audio(
    source: str,
    *,
    fps: float = 1.0,
    max_frames: int = 30,
    max_image_long_side: int | None = None,
) -> tuple[list[ImageContentPart], AudioContentPart | None]:
    """Extract video frames and audio track using ffmpeg.

    Returns (image_content_parts, audio_content_part_or_None).
    """
    if source.startswith(("http://", "https://")):
        _abort("Remote video URLs are not supported in extract mode. Download the file first.")

    path = Path(source).resolve()
    _validate_video(path)
    ffmpeg = _require_ffmpeg()

    with tempfile.TemporaryDirectory(prefix="qsense_") as tmpdir:
        tmp = Path(tmpdir)

        # --- Extract frames ---
        frames_pattern = str(tmp / "frame_%04d.jpg")
        _run_ffmpeg([
            ffmpeg, "-i", str(path),
            "-vf", f"fps={fps}",
            "-q:v", "2",
            frames_pattern,
        ])

        frame_files = sorted(tmp.glob("frame_*.jpg"))
        if not frame_files:
            _abort(f"No frames extracted from video: {path}")

        # Uniform sampling if too many frames
        if len(frame_files) > max_frames:
            step = len(frame_files) / max_frames
            frame_files = [frame_files[int(i * step)] for i in range(max_frames)]

        frame_paths = [str(f) for f in frame_files]
        if max_image_long_side:
            images = prepare_images(frame_paths, max_long_side=max_image_long_side)
        else:
            images = prepare_images(frame_paths)

        # --- Extract audio (if present) ---
        audio_part: AudioContentPart | None = None
        if _has_audio_stream(ffmpeg, path):
            audio_path = tmp / "audio.wav"
            _run_ffmpeg([
                ffmpeg, "-i", str(path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(audio_path),
            ])
            if audio_path.exists() and audio_path.stat().st_size > 0:
                audio_part = prepare_audio(str(audio_path))

        return images, audio_part
