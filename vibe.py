import sys
import os
import signal
import atexit
from pathlib import Path
from govee import GoveeLanDevice, debug_print

LOCK_FILE = Path("/tmp/vibelight.lock")


def get_lock_pid():
    """Get PID of currently running vibe.py process, if any."""
    try:
        if LOCK_FILE.exists():
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            # Check if process is actually running
            try:
                os.kill(pid, 0)
                return pid
            except (OSError, ProcessLookupError):
                # Process doesn't exist anymore
                LOCK_FILE.unlink()
                return None
    except (ValueError, FileNotFoundError):
        pass
    return None


def acquire_lock():
    """Acquire exclusive lock, terminating any existing process."""
    existing_pid = get_lock_pid()
    if existing_pid:
        debug_print(f"Terminating existing vibe.py process (PID: {existing_pid})")
        try:
            # Send SIGTERM first
            os.kill(existing_pid, signal.SIGTERM)
            # Wait a moment for graceful shutdown
            import time

            time.sleep(0.3)
            # Force kill if still running
            try:
                os.kill(existing_pid, 0)
                os.kill(existing_pid, signal.SIGKILL)
                time.sleep(0.1)
            except (OSError, ProcessLookupError):
                pass  # Process already terminated
        except (OSError, ProcessLookupError):
            pass  # Process already gone

    # Write our PID to lock file
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def release_lock():
    """Release the lock file on exit."""
    try:
        if LOCK_FILE.exists():
            with open(LOCK_FILE, "r") as f:
                pid = f.read().strip()
            if pid == str(os.getpid()):
                LOCK_FILE.unlink()
    except (FileNotFoundError, ValueError):
        pass


# Register cleanup on exit
atexit.register(release_lock)

# Discover or hard-code your Govee strip's MAC/IP once
led = GoveeLanDevice()  # auto-discovers


def set_status(status: str):
    """Set status with mode-specific breathing effects.

    Using pure RGB mode (temp=None) for better color accuracy on H607C.
    Each mode has different breathing characteristics:
    - plan: energetic orange (fast, full brightness)
    - build: balanced blue (medium, high brightness)
    - idle: calm gray (slow, relaxed brightness)
    - off: turn off the light
    """
    debug_print(f"Setting mode: {status}")

    if status == "off":
        # Turn off the light and stop any effects
        debug_print("Turning off light...")
        led.stop()
        led.off()
        return

    if status == "plan":
        # Energetic orange breathing - full brightness
        debug_print("Starting orange breathe effect...")
        led.breathe(245, 130, 40, min_bright=30, max_bright=100, speed=0.8)
    elif status == "build":
        # Balanced blue breathing - high brightness
        debug_print("Starting blue breathe effect...")
        led.breathe(70, 130, 245, min_bright=25, max_bright=90, speed=1.0)
    else:  # idle
        # Calm light gray breathing - relaxed brightness
        debug_print("Starting gray breathe effect...")
        led.breathe(240, 240, 240, min_bright=20, max_bright=70, speed=1.5)

    # Effect runs in background - return immediately for opencode plugin compatibility
    debug_print(f"Effect started for {status} mode. Running in background.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        acquire_lock()  # Ensure exclusive access
        set_status(sys.argv[1])
    else:
        print(f"Usage: python {sys.argv[0]} [plan|build|idle|off]")
