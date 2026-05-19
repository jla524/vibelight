#!/usr/bin/env python3

import json
import os
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
        debug_print("No Govee device found; skipping")
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


# Cursor hooks: stdin JSON with hook_event_name. Do not treat sessionIdle as
# idle — Cursor can emit it while the agent is still working and would override
# purple. Match names case-insensitively.
_CURSOR_AGENT = frozenset(
    {
        "beforesubmitprompt",
        "beforeshellexecution",
        "aftershellexecution",
        "beforemcpexecution",
        "aftermcpexecution",
        "beforereadfile",
        "afterfileedit",
        "afteragentresponse",
        "afteragentthought",
    }
)
_CURSOR_IDLE = frozenset(
    {
        "sessionstart",
        "sessionend",
        "stop",
    }
)


def run_cursor_hook() -> None:
    """Read Cursor hook JSON from stdin; set lamp; print {} for the hooks protocol."""
    raw = sys.stdin.read()
    try:
        payload: dict = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as e:
        print(f"[vibelight] invalid stdin JSON: {e}", file=sys.stderr)
        payload = {}

    if os.environ.get("VIBELIGHT_DEBUG"):
        print("[vibelight] stdin payload:", json.dumps(payload), file=sys.stderr)

    name = payload.get("hook_event_name")
    event = str(name).lower() if name is not None else ""

    if event in _CURSOR_IDLE:
        set_status("idle")
    elif event in _CURSOR_AGENT:
        set_status("agent")

    print("{}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cursor-hook":
        run_cursor_hook()
    elif len(sys.argv) > 1:
        set_status(sys.argv[1])
    else:
        print(f"Usage: python {sys.argv[0]} [on|plan|build|agent|idle|off|cursor-hook]")
