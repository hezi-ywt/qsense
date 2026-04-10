"""Video frame extraction backends — ffmpeg and pyav."""

from __future__ import annotations

import io
import struct
import subprocess
from pathlib import Path

from ._util import abort as _abort
from .audio import AudioContentPart, prepare_audio
from .image import ImageContentPart, prepare_images


# ---------------------------------------------------------------------------
# ffmpeg backend
# ---------------------------------------------------------------------------

def _run_ffmpeg(args: list[str]) -> None:
    try:
        subprocess.run(args, check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace").strip()
        _abort(f"ffmpeg failed: {stderr[:300]}")


def _has_audio_stream(ffmpeg: str, video_path: Path) -> bool:
    try:
        result = subprocess.run(
            [ffmpeg, "-i", str(video_path), "-hide_banner"],
            capture_output=True, text=True,
        )
        return "Audio:" in result.stderr
    except Exception:
        return False


def extract_with_ffmpeg(
    ffmpeg: str,
    path: Path,
    tmp: Path,
    fps: float,
    max_frames: int,
    max_image_long_side: int | None,
) -> tuple[list[ImageContentPart], AudioContentPart | None]:
    """Extract frames + audio using ffmpeg."""
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

    if len(frame_files) > max_frames:
        step = len(frame_files) / max_frames
        frame_files = [frame_files[int(i * step)] for i in range(max_frames)]

    frame_paths = [str(f) for f in frame_files]
    kwargs = {"max_long_side": max_image_long_side} if max_image_long_side else {}
    images = prepare_images(frame_paths, **kwargs)

    audio_part: AudioContentPart | None = None
    if _has_audio_stream(ffmpeg, path):
        audio_path = tmp / "audio.wav"
        _run_ffmpeg([
            ffmpeg, "-i", str(path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(audio_path),
        ])
        if audio_path.exists() and audio_path.stat().st_size > 0:
            audio_part = prepare_audio(str(audio_path))

    return images, audio_part


# ---------------------------------------------------------------------------
# pyav backend
# ---------------------------------------------------------------------------

def _extract_audio_pyav(path: Path, tmp: Path) -> AudioContentPart | None:
    """Extract audio track using pyav (pure Python)."""
    try:
        import av
    except ImportError:
        return None

    try:
        container = av.open(str(path))
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)
        if not audio_stream:
            container.close()
            return None

        resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
        samples: list[bytes] = []
        for frame in container.decode(audio_stream):
            for resampled in resampler.resample(frame):
                samples.append(resampled.to_ndarray().tobytes())
        container.close()

        raw_pcm = b"".join(samples)
        if len(raw_pcm) == 0:
            return None

        # Write as WAV
        buf = io.BytesIO()
        buf.write(b"RIFF")
        buf.write(struct.pack("<I", 36 + len(raw_pcm)))
        buf.write(b"WAVEfmt ")
        buf.write(struct.pack("<IHHIIHH", 16, 1, 1, 16000, 32000, 2, 16))
        buf.write(b"data")
        buf.write(struct.pack("<I", len(raw_pcm)))
        buf.write(raw_pcm)

        wav_path = tmp / "audio.wav"
        wav_path.write_bytes(buf.getvalue())
        return prepare_audio(str(wav_path))
    except Exception:
        return None


def extract_with_pyav(
    path: Path,
    tmp: Path,
    fps: float,
    max_frames: int,
    max_image_long_side: int | None,
) -> tuple[list[ImageContentPart], AudioContentPart | None]:
    """Extract frames + audio using pyav (pure Python fallback)."""
    try:
        import av
    except ImportError:
        _abort(
            "Neither ffmpeg nor pyav is available for frame extraction.\n"
            "  Install ffmpeg: qsense init (will guide you)\n"
            "  Or install pyav: pip install 'qsense-cli[video]'"
        )

    import sys
    print("[qsense] ffmpeg not found, using pyav fallback", file=sys.stderr)

    try:
        container = av.open(str(path))
        video_stream = next((s for s in container.streams if s.type == "video"), None)
        if not video_stream:
            _abort(f"No video stream found in: {path}")

        source_fps = float(video_stream.average_rate or 30)
        frame_interval = max(1, int(source_fps / fps))

        frame_paths: list[str] = []
        frame_count = 0
        for frame in container.decode(video_stream):
            if frame_count % frame_interval == 0:
                frame_path = tmp / f"frame_{len(frame_paths):04d}.jpg"
                img = frame.to_image()
                img.save(str(frame_path), format="JPEG", quality=85)
                frame_paths.append(str(frame_path))
            frame_count += 1
        container.close()
    except SystemExit:
        raise
    except Exception as exc:
        _abort(f"Cannot read video {path}: {exc}")

    if not frame_paths:
        _abort(f"No frames extracted from video: {path}")

    if len(frame_paths) > max_frames:
        step = len(frame_paths) / max_frames
        frame_paths = [frame_paths[int(i * step)] for i in range(max_frames)]

    kwargs = {"max_long_side": max_image_long_side} if max_image_long_side else {}
    images = prepare_images(frame_paths, **kwargs)
    audio_part = _extract_audio_pyav(path, tmp)

    return images, audio_part
