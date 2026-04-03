import sys
from govee import GoveeLanDevice

# Discover or hard-code your Govee strip's MAC/IP once
led = GoveeLanDevice()  # auto-discovers


def set_status(status: str):
    """Set status with colors tuned for H607C.
    
    The H607C is sensitive to color temperature. 
    Using pure RGB mode (temp=None) to avoid white channel mixing.
    """
    if status == "plan":
        # Softer orange - full brightness
        led.set_color(245, 130, 40, temp=None)
        led.set_brightness(100)
    elif status == "build":
        # Softer blue - high brightness
        led.set_color(70, 130, 245, temp=None)
        led.set_brightness(90)
    else:  # idle
        # Soft white/gray - relaxed brightness
        led.set_color(240, 240, 240, temp=6500)
        led.set_brightness(70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        set_status(sys.argv[1])
    else:
        print(f"Usage: python {sys.argv[0]} [plan|build|idle]")