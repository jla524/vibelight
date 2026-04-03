import sys
from govee import GoveeLanDevice, debug_print

# Discover or hard-code your Govee strip's MAC/IP once
led = GoveeLanDevice()  # auto-discovers


def set_status(status: str):
    """Set status with a simple solid color.

    Using pure RGB mode (temp=None) for better color accuracy on H607C.
    - plan: energetic orange
    - build: balanced blue
    - idle: calm gray
    - on: turn on the light
    - off: turn off the light
    """
    debug_print(f"Setting mode: {status}")

    if status == "on":
        debug_print("Turning on light...")
        led.on()
        return

    if status == "off":
        debug_print("Turning off light...")
        led.off()
        return

    if status == "plan":
        led.on()
        led.set_color(245, 130, 40, temp=None)
    elif status == "build":
        led.on()
        led.set_color(70, 130, 245, temp=None)
    else:  # idle
        led.on()
        led.set_color(240, 240, 240, temp=None)

    debug_print(f"Set {status} color.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        set_status(sys.argv[1])
    else:
        print(f"Usage: python {sys.argv[0]} [on|plan|build|idle|off]")
