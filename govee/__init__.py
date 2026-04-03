"""Govee LAN Control (vendored)

Original: https://github.com/srinivasansharath/govee_lan_control
MIT License - Copyright (c) Sharath Srinivasan

Added: breathe() effects with mode-specific breathing patterns
and smooth transitions between modes.
"""

from .govee_lan_device import GoveeLanDevice
from .utils import debug_print

__all__ = ["GoveeLanDevice", "debug_print"]
