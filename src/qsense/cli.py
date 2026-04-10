"""CLI entry point for qsense."""

from __future__ import annotations

import sys

import click

from . import __version__
from ._deps import check_video_deps
from .audio import prepare_audios
from .client import chat
from .config import (
    CONFIG_FILE,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    load_config,
    run_first_time_setup,
    show_config,
    update_config,
)
from .image import prepare_images
from .models import get_model, is_registered, list_models
from .video import encode_video_direct, extract_frames_and_audio


# ---------------------------------------------------------------------------
# Main command group
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="qsense")
@click.option("--prompt", default=None, help="Text prompt for the model.")
@click.option("--image", "images", multiple=True, help="Image path or URL (repeatable).")
@click.option("--audio", "audios", multiple=True, help="Audio file path or URL (repeatable).")
@click.option("--video", "videos", multiple=True, help="Video file path or URL (repeatable).")
@click.option("--video-extract", is_flag=True, default=False,
              help="Use frame extraction instead of direct passthrough (requires ffmpeg or pyav).")
@click.option("--video-passthrough", is_flag=True, default=False,
              help="Force URL passthrough for remote videos (skip download).")
@click.option("--fps", default=1.0, type=click.FloatRange(min=0.1),
              help="Frame extraction rate (default: 1). Only with --video-extract.")
@click.option("--max-frames", default=30, type=click.IntRange(min=1),
              help="Max frames to extract (default: 30). Only with --video-extract.")
@click.option("--model", default=None, help="Override the default model.")
@click.option("--timeout", default=None, type=int, help="Request timeout in seconds.")
@click.option("--max-size", default=None, type=int, help="Max image longest side in pixels (default: 2048).")
@click.pass_context
def main(
    ctx: click.Context,
    prompt: str | None,
    images: tuple[str, ...],
    audios: tuple[str, ...],
    videos: tuple[str, ...],
    video_extract: bool,
    video_passthrough: bool,
    fps: float,
    max_frames: int,
    model: str | None,
    timeout: int | None,
    max_size: int | None,
) -> None:
    """Minimal CLI multimodal understanding tool."""
    if ctx.invoked_subcommand is not None:
        return

    if not prompt or not prompt.strip():
        print("[qsense] --prompt is required.", file=sys.stderr)
        sys.exit(1)

    if not images and not audios and not videos:
        print("[qsense] At least one --image, --audio, or --video is required.", file=sys.stderr)
        sys.exit(1)

    cfg = load_config(
        model=model, timeout=timeout,
        has_image=bool(images), has_audio=bool(audios), has_video=bool(videos),
    )

    if not is_registered(cfg.model):
        click.echo(
            f"[qsense] Warning: model '{cfg.model}' is not in the registry. "
            f"Run 'qsense models' to see available models.",
            err=True,
        )

    image_kwargs = {"max_long_side": max_size} if max_size else {}
    image_content = prepare_images(images, **image_kwargs) if images else []
    audio_content = prepare_audios(audios) if audios else []

    model_info = get_model(cfg.model)
    use_passthrough = video_passthrough or (model_info.video_url_passthrough if model_info else False)
    extras: list[dict] = []

    for src in videos:
        if video_extract:
            frames, audio_part = extract_frames_and_audio(
                src, fps=fps, max_frames=max_frames, max_image_long_side=max_size,
            )
            image_content.extend(frames)
            if audio_part:
                audio_content.append(audio_part)
        else:
            extras.append(encode_video_direct(src, url_passthrough=use_passthrough))

    answer = chat(
        cfg, prompt,
        images=image_content or None,
        audios=audio_content or None,
        extras=extras or None,
    )
    print(answer)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

@main.command()
@click.option("--model", default=None, help="Set global default model.")
@click.option("--image-model", default=None, help="Set default model for image tasks.")
@click.option("--audio-model", default=None, help="Set default model for audio tasks.")
@click.option("--video-model", default=None, help="Set default model for video tasks.")
@click.option("--base-url", default=None, help="Set API base URL.")
@click.option("--api-key", default=None, help="Set API key.")
def config(
    model: str | None,
    image_model: str | None,
    audio_model: str | None,
    video_model: str | None,
    base_url: str | None,
    api_key: str | None,
) -> None:
    """Show or update persistent configuration (~/.qsense/.env)."""
    all_none = all(v is None for v in (model, image_model, audio_model, video_model, base_url, api_key))

    if all_none:
        current = show_config()
        click.echo(f"  api_key:      {current['api_key']}")
        click.echo(f"  base_url:     {current['base_url']}")
        click.echo(f"  model:        {current['model']}")
        if "image_model" in current:
            click.echo(f"  image_model:  {current['image_model']}")
        if "audio_model" in current:
            click.echo(f"  audio_model:  {current['audio_model']}")
        if "video_model" in current:
            click.echo(f"  video_model:  {current['video_model']}")
        return

    update_config(
        api_key=api_key, base_url=base_url, model=model,
        image_model=image_model, audio_model=audio_model, video_model=video_model,
    )
    updated = []
    if api_key is not None:
        updated.append("api_key")
    if base_url is not None:
        updated.append(f"base_url={base_url}")
    if model is not None:
        updated.append(f"model={model}")
    if image_model is not None:
        updated.append(f"image_model={image_model}")
    if audio_model is not None:
        updated.append(f"audio_model={audio_model}")
    if video_model is not None:
        updated.append(f"video_model={video_model}")
    click.echo(f"[qsense] Updated: {', '.join(updated)}")


@main.command()
@click.option("--api-key", default=None, help="API key (skip interactive prompt).")
@click.option("--base-url", default=None, help=f"API base URL (default: {DEFAULT_BASE_URL}).")
@click.option("--model", default=None, help=f"Default model (default: {DEFAULT_MODEL}).")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing config.")
def init(api_key: str | None, base_url: str | None, model: str | None, force: bool) -> None:
    """Initialize configuration (interactive or via flags).

    \b
    Examples:
      qsense init                                    # interactive
      qsense init --api-key sk-xxx                   # non-interactive
      qsense init --api-key sk-xxx --model gpt-5.4   # full non-interactive
    """
    if CONFIG_FILE.exists() and not force:
        current = show_config()
        click.echo(f"[qsense] Config already exists ({CONFIG_FILE}):")
        click.echo(f"  api_key:  {current['api_key']}")
        click.echo(f"  base_url: {current['base_url']}")
        click.echo(f"  model:    {current['model']}")
        click.echo()
        click.echo("Run with --force to overwrite, or use 'qsense config' to update individual fields.")
        check_video_deps()
        return

    if api_key:
        update_config(api_key=api_key, base_url=base_url or DEFAULT_BASE_URL, model=model or DEFAULT_MODEL)
        click.echo(f"[qsense] Config saved to {CONFIG_FILE}")
        final = show_config()
        click.echo(f"  api_key:  {final['api_key']}")
        click.echo(f"  base_url: {final['base_url']}")
        click.echo(f"  model:    {final['model']}")
    else:
        run_first_time_setup()

    check_video_deps()


# ---------------------------------------------------------------------------
# Models subcommand
# ---------------------------------------------------------------------------

def _format_tokens(n: int | None) -> str:
    if n is None:
        return "?"
    if n >= 1_000_000:
        return f"{n // 1_000_000}M"
    if n >= 1000:
        return f"{n // 1000}K"
    return str(n)


@main.command()
@click.option("--detail", is_flag=True, default=False, help="Show detailed limits for each model.")
def models(detail: bool) -> None:
    """List available multimodal models."""
    current = show_config()
    default_model = current["model"]

    for m in list_models():
        caps = []
        if m.vision:
            caps.append("vision")
        if m.audio:
            caps.append("audio")
        if m.video:
            caps.append("video(native)" if m.native_video else "video(extract)")

        marker = " *" if m.id == default_model else ""
        click.echo(f"  {m.id}{marker}")
        click.echo(f"    {m.name} | {', '.join(caps)} | ctx {_format_tokens(m.context_tokens)}")
        if m.description:
            click.echo(f"    {m.description}")

        if detail:
            _print_model_detail(m)

        click.echo()


def _print_model_detail(m) -> None:
    """Print detailed limits for a single model."""
    if m.vision:
        parts = []
        if m.max_image_size_mb:
            parts.append(f"max {m.max_image_size_mb}MB")
        if m.max_image_resolution:
            parts.append(f"max {m.max_image_resolution}")
        if m.max_images_per_request:
            parts.append(f"max {m.max_images_per_request}/req")
        if m.image_formats:
            parts.append(", ".join(m.image_formats))
        click.echo(f"    image: {' | '.join(parts)}")
    if m.audio:
        parts = []
        if m.max_audio_duration_min:
            parts.append(f"max {m.max_audio_duration_min}min")
        if m.audio_formats:
            parts.append(", ".join(m.audio_formats))
        click.echo(f"    audio: {' | '.join(parts)}")
    if m.video:
        parts = []
        parts.append("native" if m.native_video else "extract only")
        if m.max_video_duration_min:
            parts.append(f"max {m.max_video_duration_min}min")
        if m.video_formats:
            parts.append(", ".join(m.video_formats))
        click.echo(f"    video: {' | '.join(parts)}")
