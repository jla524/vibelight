import json
import time
import threading
import math
from . import udp
from . import discover
from .utils import debug_print

# Govee Multicast Network Parameters
MCAST_GRP = "239.255.255.250"
MCAST_SEND_PORT = 4001
MCAST_RECV_PORT = 4002
DEVICE_CONTROL_PORT = 4003


class GoveeLanDevice:
    """Control Govee LED devices over LAN using UDP multicast."""

    def __init__(self):
        ip, mac, name = discover.discover_govee_leds()
        if ip is None:
            self.isInitialized = False
            self.ip = None
            self.mac = None
            self.name = None
        else:
            self.ip = ip
            self.mac = mac
            self.name = name
            self.isInitialized = True
            debug_print(f"Discovered Govee LED device: {name} at {ip} ({mac})")

        # Initialize effect management (even if device not found)
        self._current_effect = None
        self._stop_event = threading.Event()

    def on(self):
        """Turn the light on."""
        payload = {"msg": {"cmd": "turn", "data": {"value": 1}}}
        debug_print("Turning on...")
        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)

    def off(self):
        """Turn the light off."""
        payload = {"msg": {"cmd": "turn", "data": {"value": 0}}}
        debug_print("Turning off...")
        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)

    def set_brightness(self, brightness):
        """Set brightness (0-100)."""
        brightness = max(0, min(100, int(brightness)))
        payload = {"msg": {"cmd": "brightness", "data": {"value": brightness}}}
        debug_print(f"Setting brightness to {brightness}%...")
        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)

    def set_color(self, r, g, b, temp=None):
        """Set color. For H607C, color temperature affects white channel mixing.
        temp=None: pure RGB mode (no white channel)
        temp=0: disable white channel explicitly"""
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))

        if temp is None or temp == 0:
            # Pure RGB mode - use temp=0 to disable white channel
            payload = {
                "msg": {
                    "cmd": "colorwc",
                    "data": {
                        "color": {"r": r, "g": g, "b": b},
                        "colorTemInKelvin": 0,  # Explicitly disable white
                    },
                }
            }
            debug_print(f"Setting pure RGB({r},{g},{b})")
        else:
            temp = max(2700, min(9000, int(temp)))
            payload = {
                "msg": {
                    "cmd": "colorwc",
                    "data": {
                        "color": {"r": r, "g": g, "b": b},
                        "colorTemInKelvin": temp,
                    },
                }
            }
            debug_print(f"Setting RGB({r},{g},{b}) @ {temp}K...")

        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)

    def blink(self, reps=1):
        """Blink the light."""
        current_state = self.get_status()
        if not current_state:
            return

        if current_state["onOff"] == 0:
            for _ in range(reps):
                self.on()
                time.sleep(1)
                self.off()
                time.sleep(1)
        else:
            for _ in range(reps):
                self.off()
                time.sleep(1)
                self.on()
                time.sleep(1)

    def get_status(self):
        """Get current device status."""
        payload = {"msg": {"cmd": "devStatus", "data": {}}}
        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)
        data, addr = udp.receive_udp_packet(MCAST_GRP, MCAST_RECV_PORT, 3)

        if data:
            status = json.loads(data.decode("utf-8"))["msg"]["data"]
            return {
                "onOff": status.get("onOff", 0),
                "brightness": status.get("brightness", 0),
                "r": status.get("color", {}).get("r", 0),
                "g": status.get("color", {}).get("g", 0),
                "b": status.get("color", {}).get("b", 0),
                "colorTemp": status.get("colorTemInKelvin", 6500),
            }
        return None

    def stop(self):
        """Stop any currently running effect."""
        if self._current_effect and self._current_effect.is_alive():
            self._stop_event.set()
            self._current_effect.join(timeout=1.0)
            self._current_effect = None
            self._stop_event.clear()
        debug_print("Stopped current effect.")

    def _breathe_thread(self, color, min_bright, max_bright, speed):
        """Background thread for breathing effect."""
        r, g, b = color
        phase = 0.0

        while not self._stop_event.is_set():
            # Calculate breathing brightness using sine wave
            brightness = (
                min_bright + (max_bright - min_bright) * (math.sin(phase) + 1) / 2
            )
            brightness = int(brightness)

            # Set color and brightness - use pure RGB mode (temp=None) for H607C
            self.set_color(r, g, b, temp=None)
            self.set_brightness(brightness)

            phase += 0.1 * speed
            time.sleep(0.05)  # ~20 updates per second for smooth breathing

    def breathe(self, r, g, b, min_bright=20, max_bright=85, speed=2.0):
        """Start breathing effect with given color and parameters."""
        if not self.isInitialized:
            debug_print("Device not initialized.")
            return

        # Stop any existing effect
        self.stop()

        # Small delay to ensure previous effect is fully stopped
        time.sleep(0.2)

        # Set initial color immediately so user sees the change
        self.set_color(r, g, b, temp=None)
        self.set_brightness(min_bright)

        debug_print(
            f"Starting breathe effect with RGB({r},{g},{b}), range {min_bright}-{max_bright}, speed {speed}"
        )

        self._stop_event.clear()
        self._current_effect = threading.Thread(
            target=self._breathe_thread,
            args=((r, g, b), min_bright, max_bright, speed),
            daemon=True,
        )
        self._current_effect.start()

    def fade_to(self, r, g, b, duration=1.5):
        """Smooth fade to a target color over specified duration."""
        if not self.isInitialized:
            return

        steps = 20
        delay = duration / steps

        for i in range(steps + 1):
            if self._stop_event.is_set():
                break
            factor = i / steps
            current_r = int(255 * (1 - factor) + r * factor)
            current_g = int(255 * (1 - factor) + g * factor)
            current_b = int(255 * (1 - factor) + b * factor)
            self.set_color(current_r, current_g, current_b, 6500)
            time.sleep(delay)
