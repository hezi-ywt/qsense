"""Public Python API for QSense.

Usage::

    from qsense import chat

    # Text only
    response = chat("What is 2+2?")

    # With images
    response = chat("What is in this image?", images=["photo.png"])

    # With audio
    response = chat("Transcribe this audio", audios=["recording.wav"])

Returns the assistant's text response. Exits on config/API errors (call from CLI).
"""

from __future__ import annotations

from .config import load_config
from .client import chat as _client_chat
from .image import prepare_images
from .audio import prepare_audios


def chat(
    prompt: str,
    *,
    images: list[str] | tuple[str, ...] | None = None,
    audios: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Send a multimodal message and get a text response.

    Args:
        prompt: The question or instruction.
        images: Local file paths or URLs to images.
        audios: Local file paths or URLs to audio files.

    Returns:
        The assistant's text response.
    """
    config = load_config(
        has_image=bool(images),
        has_audio=bool(audios),
    )

    prepared_images = prepare_images(images) if images else None
    prepared_audios = prepare_audios(audios) if audios else None

    return _client_chat(
        config=config,
        prompt=prompt,
        images=prepared_images,
        audios=prepared_audios,
    )
