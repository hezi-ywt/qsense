"""Probe which audio content format the API accepts.

Usage:
    QSENSE_API_KEY=xxx python scripts/probe_audio_format.py

Generates a short sine-wave WAV, then tries two payload formats against
gemini-3-flash-preview to find which one works.
"""

from __future__ import annotations

import base64
import io
import struct
import sys

from openai import OpenAI

BASE_URL = "https://api.openai.com/v1"
MODEL = "gemini-3-flash-preview"
PROMPT = "Describe what you hear in this audio."


# ---------------------------------------------------------------------------
# Generate a tiny WAV (1 second, 440 Hz sine wave)
# ---------------------------------------------------------------------------

def make_sine_wav(freq: int = 440, duration: float = 1.0, sample_rate: int = 16000) -> bytes:
    import math

    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        value = int(32767 * 0.5 * math.sin(2 * math.pi * freq * t))
        samples.append(struct.pack("<h", value))

    raw = b"".join(samples)
    buf = io.BytesIO()
    # WAV header
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(raw)))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))       # chunk size
    buf.write(struct.pack("<H", 1))        # PCM
    buf.write(struct.pack("<H", 1))        # mono
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", sample_rate * 2))  # byte rate
    buf.write(struct.pack("<H", 2))        # block align
    buf.write(struct.pack("<H", 16))       # bits per sample
    buf.write(b"data")
    buf.write(struct.pack("<I", len(raw)))
    buf.write(raw)
    return buf.getvalue()


def get_api_key() -> str:
    import os
    key = os.environ.get("QSENSE_API_KEY", "")
    if not key:
        print("Set QSENSE_API_KEY env var first.", file=sys.stderr)
        sys.exit(1)
    return key


def try_format(client: OpenAI, label: str, content: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"Testing: {label}")
    print(f"{'='*60}")
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": content}],
            timeout=30,
        )
        text = resp.choices[0].message.content if resp.choices else "(no text)"
        print(f"SUCCESS — response: {text[:200]}")
    except Exception as exc:
        print(f"FAILED  — {exc}")


def main() -> None:
    api_key = get_api_key()
    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    wav_bytes = make_sine_wav()
    b64 = base64.b64encode(wav_bytes).decode()
    data_url = f"data:audio/wav;base64,{b64}"

    print(f"WAV size: {len(wav_bytes)} bytes, base64 length: {len(b64)}")

    # --- Format A: OpenAI input_audio ---
    content_a = [
        {"type": "text", "text": PROMPT},
        {
            "type": "input_audio",
            "input_audio": {"data": b64, "format": "wav"},
        },
    ]
    try_format(client, "Format A: input_audio (OpenAI native)", content_a)

    # --- Format B: data URL via image_url field ---
    content_b = [
        {"type": "text", "text": PROMPT},
        {
            "type": "image_url",
            "image_url": {"url": data_url},
        },
    ]
    try_format(client, "Format B: data URL in image_url field", content_b)

    # --- Format C: inline_data (Gemini style via some proxies) ---
    content_c = [
        {"type": "text", "text": PROMPT},
        {
            "type": "audio_url",
            "audio_url": {"url": data_url},
        },
    ]
    try_format(client, "Format C: audio_url field", content_c)


if __name__ == "__main__":
    main()
