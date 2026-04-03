"""Utility functions for govee package."""

import os


_DEBUG_MODE = os.environ.get("VIBELIGHT_DEBUG", "").lower() in ("1", "true", "yes")


def debug_print(*args, **kwargs):
    """Print only when VIBELIGHT_DEBUG environment variable is set."""
    if _DEBUG_MODE:
        print(*args, **kwargs)
