"""Audio normalization — validate, download if remote, encode for API.

Uses data URL via image_url field (``data:audio/wav;base64,...``) for
best proxy compatibility. Remote URLs are downloaded via ``_download.py``.
"""

from __future__ import annotations

import base64
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from ._download import stream_download
from ._util import abort as _abort

# ---------------------------------------------------------------------------
# Supported formats
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".webm"}

EXTENSION_TO_MIME: dict[str, str] = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".webm": "audio/webm",
}

MIME_TO_FORMAT: dict[str, str] = {
    "audio/mpeg": "mp3", "audio/mp3": "mp3",
    "audio/wav": "wav", "audio/x-wav": "wav",
    "audio/flac": "flac", "audio/ogg": "ogg",
    "audio/mp4": "m4a", "audio/m4a": "m4a",
    "audio/aac": "aac", "audio/webm": "webm",
}

DOWNLOAD_MAX_BYTES = 20 * 1024 * 1024  # 20 MB

# Return type alias (can be data URL or input_audio format)
AudioContentPart = dict


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _to_data_url_part(raw: bytes, mime: str) -> dict:
    """Encode as data URL in image_url field (best compatibility)."""
    encoded = base64.b64encode(raw).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}


def _infer_mime_from_url(url: str) -> str | None:
    ext = PurePosixPath(urlparse(url).path).suffix.lower()
    return EXTENSION_TO_MIME.get(ext)


def _download_and_encode(url: str) -> dict:
    """Download a remote audio file, detect format, encode."""
    raw, content_type = stream_download(
        url, max_bytes=DOWNLOAD_MAX_BYTES, timeout=60, label="audio",
    )

    mime = content_type if content_type in MIME_TO_FORMAT else _infer_mime_from_url(url)
    if not mime:
        _abort(f"Cannot determine audio format for {url} (Content-Type: {content_type})")

    return _to_data_url_part(raw, mime)


def _load_and_encode(path: Path) -> dict:
    """Read a local audio file, validate, encode."""
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        _abort(f"Unsupported audio type: {path}")

    try:
        raw = path.read_bytes()
    except Exception as exc:
        _abort(f"Cannot read audio {path}: {exc}")

    if len(raw) == 0:
        _abort(f"Audio file is empty: {path}")

    return _to_data_url_part(raw, EXTENSION_TO_MIME[ext])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def prepare_audio(source: str) -> dict:
    """Turn one ``--audio`` argument into an API content part.

    Uses data URL via image_url field for best proxy compatibility.
    Remote URLs are downloaded first.
    """
    if source.startswith(("http://", "https://")):
        return _download_and_encode(source)

    path = Path(source).resolve()
    if not path.exists():
        _abort(f"Audio file not found: {path}")

    return _load_and_encode(path)


def prepare_audios(sources: tuple[str, ...] | list[str]) -> list[dict]:
    """Prepare multiple audio sources, preserving order."""
    return [prepare_audio(s) for s in sources]
