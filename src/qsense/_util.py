"""Shared internal utilities."""

from __future__ import annotations

import sys


def abort(message: str) -> None:
    """Print a prefixed error to stderr and exit with status 1."""
    print(f"[qsense] {message}", file=sys.stderr)
    sys.exit(1)
