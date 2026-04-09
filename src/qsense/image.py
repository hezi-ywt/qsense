"""Image normalization — validate, resize, and encode to data URL."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import TypedDict

from PIL import Image

from ._util import abort as _abort

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class ImageURL(TypedDict):
    url: str


class ImageContentPart(TypedDict):
    type: str
    image_url: ImageURL


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

EXTENSION_TO_MIME: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

IMAGE_MAX_LONG_SIDE = 2048
IMAGE_MIN_SIDE = 64
IMAGE_ENCODE_QUALITY = 85


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _fit_to_limit(img: Image.Image, max_long_side: int) -> Image.Image:
    """Shrink so the longest side <= *max_long_side*. Never upscale."""
    width, height = img.size
    long_side = max(width, height)
    if long_side <= max_long_side:
        return img
    scale = max_long_side / long_side
    new_width = max(int(width * scale), 1)
    new_height = max(int(height * scale), 1)
    return img.resize((new_width, new_height), Image.LANCZOS)


def _encode_to_data_url(img: Image.Image, mime: str) -> str:
    """Encode a PIL Image as a base64 data-URL string."""
    buf = io.BytesIO()

    if mime == "image/jpeg":
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=IMAGE_ENCODE_QUALITY)
    elif mime == "image/webp":
        img.save(buf, format="WEBP", quality=IMAGE_ENCODE_QUALITY)
    elif mime == "image/gif":
        img.save(buf, format="PNG")
        mime = "image/png"
    else:
        img.save(buf, format="PNG")

    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:{mime};base64,{encoded}"


def _load_and_process(
    path: Path,
    max_long_side: int,
) -> ImageContentPart:
    """Open a local image file → validate → resize → encode."""
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        _abort(f"Unsupported image type: {path}")

    mime = EXTENSION_TO_MIME[ext]

    try:
        img = Image.open(path)
        img.load()
    except Exception as exc:
        _abort(f"Cannot read image {path}: {exc}")

    width, height = img.size
    if width < IMAGE_MIN_SIDE or height < IMAGE_MIN_SIDE:
        _abort(f"Image too small ({width}x{height}): {path}")

    img = _fit_to_limit(img, max_long_side)
    data_url = _encode_to_data_url(img, mime)
    return {"type": "image_url", "image_url": {"url": data_url}}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def prepare_image(
    source: str,
    *,
    max_long_side: int = IMAGE_MAX_LONG_SIDE,
) -> ImageContentPart:
    """Turn one ``--image`` argument into an OpenAI-compatible content part.

    * Remote URL → pass through unchanged.
    * Local path → validate, resize if oversized, base64-encode.
    """
    if source.startswith(("http://", "https://")):
        return {"type": "image_url", "image_url": {"url": source}}

    path = Path(source).resolve()
    if not path.exists():
        _abort(f"Image file not found: {path}")

    return _load_and_process(path, max_long_side)


def prepare_images(
    sources: tuple[str, ...] | list[str],
    *,
    max_long_side: int = IMAGE_MAX_LONG_SIDE,
) -> list[ImageContentPart]:
    """Prepare multiple images, preserving order."""
    return [prepare_image(s, max_long_side=max_long_side) for s in sources]
