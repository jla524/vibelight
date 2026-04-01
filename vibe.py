import sys
import time
from govee import GoveeLanDevice

# Discover or hard-code your Govee strip's MAC/IP once
led = GoveeLanDevice()  # auto-discovers


def set_status(status: str):
    """Set status with mode-specific breathing effects.

    Each mode uses a different breathing pattern:
    - plan: energetic orange (fast, high brightness)
    - build: balanced blue (medium)
    - idle: calm gray (slow, gentle)
    """
    if status == "plan":
        # Energetic orange breathing
        led.breathe(245, 167, 66, min_bright=30, max_bright=100, speed=1.5)
    elif status == "build":
        # Balanced blue breathing
        led.breathe(92, 156, 245, min_bright=20, max_bright=85, speed=2.0)
    else:  # idle
        # Calm light gray breathing
        led.breathe(238, 238, 238, min_bright=15, max_bright=60, speed=3.0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        set_status(sys.argv[1])
    else:
        print(f"Usage: python {sys.argv[0]} [plan|build|idle]")
