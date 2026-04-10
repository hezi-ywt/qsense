"""Runtime dependency detection and installation guidance."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys

import click


def has_ffmpeg() -> str | None:
    """Return ffmpeg path if available, None otherwise."""
    return shutil.which("ffmpeg")


def has_pyav() -> bool:
    """Check if pyav (av) is importable."""
    try:
        import av  # noqa: F401
        return True
    except ImportError:
        return False


def check_video_deps() -> None:
    """Check video extraction dependencies and guide the user."""
    ffmpeg = has_ffmpeg()
    pyav = has_pyav()

    if ffmpeg:
        click.echo(f"[qsense] video extract: ffmpeg ({ffmpeg})" + (" + pyav" if pyav else ""))
        return

    if pyav:
        click.echo("[qsense] video extract: pyav (pure Python, frames + audio)")
        click.echo("  Tip: install ffmpeg for faster extraction")
        return

    # Neither available
    click.echo("[qsense] video extract: not available")
    click.echo("  Video direct mode (--video) works without any extra dependencies.")
    click.echo("  Frame extraction (--video-extract) needs ffmpeg or pyav.")
    click.echo()

    options = _ffmpeg_install_options()

    if options:
        click.echo("  Options:")
        click.echo("    1) Install ffmpeg (recommended, fastest)")
        click.echo("    2) Install pyav via pip (pure Python, no system deps)")
        click.echo("    3) Skip (video direct mode still works)")
        click.echo()

        choice = click.prompt("  Choose", type=click.Choice(["1", "2", "3"]), default="3")

        if choice == "1":
            cmd, hint = options[0]
            _run_install(cmd, hint)
            return
        elif choice == "2":
            _install_pyav()
            return
    else:
        click.echo("  Options:")
        click.echo("    1) Install pyav via pip (pure Python, no system deps)")
        click.echo("    2) Skip (video direct mode still works)")
        click.echo()

        choice = click.prompt("  Choose", type=click.Choice(["1", "2"]), default="2")

        if choice == "1":
            _install_pyav()
            return

    click.echo("[qsense] Skipped. You can always install later:")
    click.echo("  pip install 'qsense-cli[video]'  # pyav")
    click.echo("  # or install ffmpeg for your platform")


def _ffmpeg_install_options() -> list[tuple[list[str], str]]:
    """Return available ffmpeg install commands for the current platform."""
    os_name = platform.system()
    if os_name == "Darwin" and shutil.which("brew"):
        return [(["brew", "install", "ffmpeg"], "brew install ffmpeg")]
    if os_name == "Linux" and shutil.which("apt"):
        return [(["sudo", "apt", "install", "-y", "ffmpeg"], "sudo apt install ffmpeg")]
    if os_name == "Windows":
        if shutil.which("winget"):
            return [(["winget", "install", "Gyan.FFmpeg"], "winget install Gyan.FFmpeg")]
        if shutil.which("choco"):
            return [(["choco", "install", "ffmpeg", "-y"], "choco install ffmpeg -y")]
        if shutil.which("scoop"):
            return [(["scoop", "install", "ffmpeg"], "scoop install ffmpeg")]
    return []


def _run_install(cmd: list[str], fallback_hint: str) -> None:
    """Run an install command, show fallback on failure."""
    click.echo(f"  Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        click.echo("[qsense] ffmpeg installed.")
    except subprocess.CalledProcessError:
        click.echo(f"[qsense] Installation failed. Try manually: {fallback_hint}", err=True)


def _install_pyav() -> None:
    """Install pyav via pip."""
    click.echo("  Installing pyav...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "av>=12.0"],
            check=True, capture_output=True,
        )
        click.echo("[qsense] pyav installed.")
    except subprocess.CalledProcessError:
        click.echo("[qsense] Failed. Try manually: pip install 'qsense-cli[video]'", err=True)
