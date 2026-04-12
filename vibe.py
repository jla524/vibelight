#!/usr/bin/env python3

import json
import os
import signal
import sys
import time
from pathlib import Path

from govee import GoveeLanDevice, debug_print

PID_FILE = Path.home() / ".vibelight.pid"

led = GoveeLanDevice()


def cleanup(signum=None, frame=None):
    """Clean up effect threads and PID file on exit."""
    if led.isInitialized:
        debug_print("Cleaning up...")
        led.stop_effect()
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
            debug_print(f"Removed PID file {PID_FILE}")
        except Exception as e:
            debug_print(f"Failed to remove PID file: {e}")


def stop_existing_process():
    """Check for and stop any existing vibelight process."""
    if not PID_FILE.exists():
        return
    try:
        old_pid = int(PID_FILE.read_text().strip())
        debug_print(f"Found existing PID {old_pid}")
        try:
            os.kill(old_pid, signal.SIGTERM)
            debug_print(f"Sent SIGTERM to {old_pid}")
            time.sleep(0.3)
        except ProcessLookupError:
            debug_print(f"Process {old_pid} not running")
        except PermissionError:
            debug_print(f"No permission to kill {old_pid}")
        try:
            PID_FILE.unlink()
        except Exception:
            pass
    except (ValueError, OSError) as e:
        debug_print(f"Invalid PID file: {e}")
        try:
            PID_FILE.unlink()
        except Exception:
            pass


def write_pid_file():
    """Write current PID to file."""
    try:
        PID_FILE.write_text(str(os.getpid()))
        debug_print(f"Wrote PID {os.getpid()} to {PID_FILE}")
    except Exception as e:
        debug_print(f"Failed to write PID file: {e}")


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def set_status(status: str, foreground: bool = False):
    """Set status with mode-specific breathing effects.

    Fixed color + sine-modulated brightness (more reliable on H607C).
    - plan: energetic orange (slow pulse)
    - build: balanced blue (slow pulse)
    - agent: creative purple (slow pulse)
    - idle: calm gray (solid, no pulse)
    - on/off: solid

    Args:
        status: Mode name
        foreground: If True, keep process alive to sustain breathing effect
    """
    if not led.isInitialized:
        print("Error: No Govee device found")
        return

    debug_print(f"Setting mode: {status}")

    stop_existing_process()

    if status == "on":
        debug_print("Turning on light...")
        led.on()
        return

    if status == "off":
        debug_print("Turning off light...")
        led.off()
        return

    if status == "idle":
        debug_print("Setting idle (solid gray)...")
        led.set_color(240, 240, 240, temp=None)
        led.set_brightness(65)
        return

    write_pid_file()

    if status == "plan":
        led.set_mode_color(245, 130, 40, period=3.5, min_brightness=42)
    elif status == "build":
        led.set_mode_color(70, 130, 245, period=4.0, min_brightness=48)
    elif status == "agent":
        led.set_mode_color(150, 50, 200, period=3.8, min_brightness=45)

    debug_print(f"Set {status} breathing effect.")

    if foreground:
        debug_print("Running in foreground (keep-alive)...")
        try:
            signal.pause()
        except KeyboardInterrupt:
            pass


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
        set_status("idle", foreground=False)
    elif event in _CURSOR_AGENT:
        set_status("agent", foreground=False)

    print("{}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cursor-hook":
        run_cursor_hook()
    elif len(sys.argv) > 1:
        mode = sys.argv[1]
        foreground = mode in ("plan", "build", "agent")
        set_status(mode, foreground=foreground)
    else:
        print(f"Usage: python {sys.argv[0]} [on|plan|build|agent|idle|off|cursor-hook]")
