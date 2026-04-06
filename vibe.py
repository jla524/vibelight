#!/usr/bin/env python3

import signal
import sys
from govee import GoveeLanDevice, debug_print

# Discover or hard-code your Govee strip's MAC/IP once
led = GoveeLanDevice()  # auto-discovers


def cleanup(signum=None, frame=None):
    """Clean up effect threads on exit."""
    if led.isInitialized:
        debug_print("Cleaning up...")
        led.stop_effect()


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def set_status(status: str):
    """Set status with mode-specific colors.

    Using pure RGB mode (temp=None) for better color accuracy on H607C.
    - plan: energetic orange
    - build: balanced blue
    - agent: creative purple (for Cursor agent mode)
    - idle: calm gray
    - on: turn on the light
    - off: turn off the light
    """
    if not led.isInitialized:
        print("Error: No Govee device found")
        return

    debug_print(f"Setting mode: {status}")

    if status == "on":
        debug_print("Turning on light...")
        led.stop_effect()
        led.on()
        return

    if status == "off":
        debug_print("Turning off light...")
        led.stop_effect()
        led.off()
        return

    if status == "plan":
        led.set_mode_color(245, 130, 40)
    elif status == "build":
        led.set_mode_color(70, 130, 245)
    elif status == "agent":
        led.set_mode_color(150, 50, 200)
    else:  # idle
        led.set_mode_color(240, 240, 240)

    debug_print(f"Set {status} color.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        set_status(sys.argv[1])
    else:
        print(f"Usage: python {sys.argv[0]} [on|plan|build|agent|idle|off]")
