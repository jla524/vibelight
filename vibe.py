import sys
import time
from govee import GoveeLanDevice

# Discover or hard-code your Govee strip's MAC/IP once
led = GoveeLanDevice()  # auto-discovers
led.set_brightness(40)


def set_status(status: str):
    if status == "plan":
        led.set_color(245, 167, 66)  # orange
        led.set_brightness(40)
    elif status == "build":
        led.set_color(92, 156, 245)  # blue
    else:  # idle
        led.set_color(238, 238, 238)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        set_status(sys.argv[1])
    else:
        print(f"Usage: python {sys.argv[0]} [plan|build|idle]")
