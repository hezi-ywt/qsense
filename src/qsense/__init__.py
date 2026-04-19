"""QSense — minimal multimodal understanding tool."""

from __future__ import annotations

from .api import chat, prepare_images, prepare_audios
from .image import SUPPORTED_EXTENSIONS as IMAGE_EXTENSIONS
from .audio import SUPPORTED_EXTENSIONS as AUDIO_EXTENSIONS

__version__ = "0.2.1"

__all__ = [
    "chat",
    "prepare_images",
    "prepare_audios",
    "IMAGE_EXTENSIONS",
    "AUDIO_EXTENSIONS",
]
