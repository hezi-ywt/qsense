"""Shared streaming download logic for audio and video."""

from __future__ import annotations

import httpx

from ._util import abort as _abort

DEFAULT_TIMEOUT = 120


def stream_download(
    url: str,
    *,
    max_bytes: int,
    timeout: int = DEFAULT_TIMEOUT,
    label: str = "file",
) -> tuple[bytes, str]:
    """Stream-download a URL with size limit.

    Returns (raw_bytes, content_type).
    Aborts if file is empty or exceeds max_bytes.
    """
    max_mb = max_bytes // 1024 // 1024
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()

                chunks: list[bytes] = []
                downloaded = 0
                for chunk in resp.iter_bytes(chunk_size=256 * 1024):
                    downloaded += len(chunk)
                    if downloaded > max_bytes:
                        _abort(f"{label} too large (>{max_mb} MB): {url}")
                    chunks.append(chunk)
    except SystemExit:
        raise
    except Exception as exc:
        _abort(f"Failed to download {label}: {url} ({exc})")

    raw = b"".join(chunks)
    if len(raw) == 0:
        _abort(f"Downloaded {label} is empty: {url}")

    return raw, content_type
