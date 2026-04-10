"""Video processing — direct passthrough and frame extraction.

Direct mode: encode whole video as base64 data URL (default).
Extract mode: split into frames + audio via ffmpeg or pyav fallback.

Extraction backends live in ``_extract.py``.
Download logic lives in ``_download.py``.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from ._deps import has_ffmpeg
from ._download import stream_download
from ._extract import extract_with_ffmpeg, extract_with_pyav
from ._util import abort as _abort
from .audio import AudioContentPart
from .image import ImageContentPart

SUPPORTED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}

EXTENSION_TO_MIME: dict[str, str] = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
}

MIME_TO_EXT: dict[str, str] = {v: k for k, v in EXTENSION_TO_MIME.items()}

DIRECT_MAX_BYTES = 20 * 1024 * 1024   # 20 MB
EXTRACT_MAX_BYTES = 100 * 1024 * 1024  # 100 MB (larger for extract mode)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_video(path: Path) -> None:
    if not path.exists():
        _abort(f"Video file not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        _abort(f"Unsupported video type: {path}")


def _infer_ext_from_url(url: str) -> str | None:
    ext = PurePosixPath(urlparse(url).path).suffix.lower()
    return ext if ext in SUPPORTED_EXTENSIONS else None


def _download_to_tempfile(url: str, tmpdir: Path, max_bytes: int) -> Path:
    """Download a remote video to a temp file."""
    raw, _ = stream_download(url, max_bytes=max_bytes, label="video")
    ext = _infer_ext_from_url(url) or ".mp4"
    tmp_path = tmpdir / f"remote_video{ext}"
    tmp_path.write_bytes(raw)
    return tmp_path


# ---------------------------------------------------------------------------
# Direct mode
# ---------------------------------------------------------------------------

def encode_video_direct(source: str, *, url_passthrough: bool = False) -> dict:
    """Encode a video as a content part.

    * Remote URL + passthrough → pass URL directly.
    * Remote URL (default) → download + base64 data URL.
    * Local path → read + base64 data URL.
    """
    if source.startswith(("http://", "https://")):
        if url_passthrough:
            return {"type": "image_url", "image_url": {"url": source}}
        raw, content_type = stream_download(source, max_bytes=DIRECT_MAX_BYTES, label="video")
        mime = content_type if content_type in MIME_TO_EXT else "video/mp4"
        encoded = base64.b64encode(raw).decode()
        return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}

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
# Extract mode
# ---------------------------------------------------------------------------

def extract_frames_and_audio(
    source: str,
    *,
    fps: float = 1.0,
    max_frames: int = 30,
    max_image_long_side: int | None = None,
) -> tuple[list[ImageContentPart], AudioContentPart | None]:
    """Extract video frames and optionally audio track.

    Uses ffmpeg if available (fastest). Falls back to pyav (pure Python).
    Supports both local files and remote URLs.
    """
    with tempfile.TemporaryDirectory(prefix="qsense_") as tmpdir:
        tmp = Path(tmpdir)

        # Resolve source to local path
        if source.startswith(("http://", "https://")):
            path = _download_to_tempfile(source, tmp, EXTRACT_MAX_BYTES)
        else:
            path = Path(source).resolve()
            _validate_video(path)

        # Choose backend
        ffmpeg = has_ffmpeg()
        if ffmpeg:
            return extract_with_ffmpeg(ffmpeg, path, tmp, fps, max_frames, max_image_long_side)
        else:
            return extract_with_pyav(path, tmp, fps, max_frames, max_image_long_side)
