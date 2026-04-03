import signal
import sys
from govee import GoveeLanDevice, debug_print, acquire_lock

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

    if status == "on":
        debug_print("Turning on light...")
        led.stop()
        led.on()
        return

    if status == "off":
        # Turn off the light and stop any effects
        debug_print("Turning off light...")
        led.stop()
        led.off()
        return

    if status == "plan":
        # Energetic orange breathing - full brightness
        debug_print("Starting orange breathe effect...")
        led.breathe(245, 130, 40, min_bright=30, max_bright=100, speed=1.5)
    elif status == "build":
        # Balanced blue breathing - high brightness
        debug_print("Starting blue breathe effect...")
        led.breathe(70, 130, 245, min_bright=25, max_bright=90, speed=1.0)
    else:  # idle
        # Calm light gray breathing - relaxed brightness
        debug_print("Starting gray breathe effect...")
        led.breathe(240, 240, 240, min_bright=20, max_bright=70, speed=0.6)

    # Effect runs in background - return immediately for opencode plugin compatibility
    debug_print(f"Effect started for {status} mode. Running in background.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if not acquire_lock():
            sys.exit(0)
        set_status(sys.argv[1])
        if sys.argv[1] != "off":
            signal.pause()
    else:
        print(f"Usage: python {sys.argv[0]} [on|plan|build|idle|off]")
