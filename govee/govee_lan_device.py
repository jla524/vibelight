import json
import threading
import time
from . import udp
from . import discover
from .utils import debug_print

# Govee Multicast Network Parameters
MCAST_GRP = "239.255.255.250"
MCAST_RECV_PORT = 4002
DEVICE_CONTROL_PORT = 4003

# Retry settings for busy device
DEVICE_BUSY_RETRY_DELAY = 0.05
MAX_DEVICE_RETRIES = 2


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
        self._effect_stop_event = threading.Event()
        self._effect_thread = None

    def _send_command(self, payload):
        """Send command with built-in retry for busy device scenarios.

        Returns True on success, False on failure (after all retries).
        """
        if not self.isInitialized or not self.ip:
            debug_print("Cannot send command: device not initialized")
            return False

        for attempt in range(MAX_DEVICE_RETRIES):
            try:
                success = udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)
                if success:
                    return True

                if attempt < MAX_DEVICE_RETRIES - 1:
                    delay = DEVICE_BUSY_RETRY_DELAY * (2**attempt)
                    debug_print(
                        f"Command failed, retrying in {delay:.2f}s (attempt {attempt + 1}/{MAX_DEVICE_RETRIES})"
                    )
                    time.sleep(delay)
            except Exception as e:
                debug_print(f"Error sending command: {e}")
                if attempt < MAX_DEVICE_RETRIES - 1:
                    delay = DEVICE_BUSY_RETRY_DELAY * (2**attempt)
                    time.sleep(delay)

        debug_print(f"Command failed after {MAX_DEVICE_RETRIES} attempts")
        return False

    def is_responsive(self, timeout=2):
        """Check if device is responsive by sending a status request."""
        if not self.isInitialized or not self.ip:
            return False

        try:
            payload = {"msg": {"cmd": "devStatus", "data": {}}}
            success = udp.send_udp_packet(
                self.ip, DEVICE_CONTROL_PORT, payload, retries=1
            )
            if not success:
                return False

            data, addr = udp.receive_udp_packet(
                MCAST_GRP, MCAST_RECV_PORT, timeout, retries=1
            )
            if data:
                try:
                    json.loads(data.decode("utf-8"))
                    return True
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return False
            return False
        except Exception as e:
            debug_print(f"Device responsiveness check failed: {e}")
            return False

    def on(self):
        """Turn the light on."""
        payload = {"msg": {"cmd": "turn", "data": {"value": 1}}}
        debug_print("Turning on...")
        self._send_command(payload)

    def off(self):
        """Turn the light off."""
        payload = {"msg": {"cmd": "turn", "data": {"value": 0}}}
        debug_print("Turning off...")
        self._send_command(payload)

    def set_brightness(self, brightness):
        """Set brightness (0-100)."""
        brightness = max(0, min(100, int(brightness)))
        payload = {"msg": {"cmd": "brightness", "data": {"value": brightness}}}
        debug_print(f"Setting brightness to {brightness}%...")
        self._send_command(payload)

    def set_color(self, r, g, b, temp=None):
        """Set color. For H607C, color temperature affects white channel mixing.
        temp=None: pure RGB mode (no white channel)
        temp=0: disable white channel explicitly

        Returns True on success, False on failure.
        """
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))

        if temp is None or temp == 0:
            payload = {
                "msg": {
                    "cmd": "colorwc",
                    "data": {
                        "color": {"r": r, "g": g, "b": b},
                        "colorTemInKelvin": 0,
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

        return self._send_command(payload)

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
        """Get current device status with error handling."""
        if not self.isInitialized or not self.ip:
            debug_print("Cannot get status: device not initialized")
            return None

        try:
            payload = {"msg": {"cmd": "devStatus", "data": {}}}
            data, addr = udp.send_and_receive_udp_packet(
                MCAST_GRP, MCAST_RECV_PORT, payload, timeout=3, multicast=True
            )

            if data:
                try:
                    status = json.loads(data.decode("utf-8"))["msg"]["data"]
                    return {
                        "onOff": status.get("onOff", 0),
                        "brightness": status.get("brightness", 0),
                        "r": status.get("color", {}).get("r", 0),
                        "g": status.get("color", {}).get("g", 0),
                        "b": status.get("color", {}).get("b", 0),
                        "colorTemp": status.get("colorTemInKelvin", 6500),
                    }
                except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
                    debug_print(f"Failed to parse status response: {e}")
                    return None
            return None
        except Exception as e:
            debug_print(f"Error getting status: {e}")
            return None

    def fade_to(self, r, g, b, duration=1.5):
        """Smooth fade to a target color over specified duration."""
        if not self.isInitialized:
            return

        current = self.get_status()
        if current:
            start_r, start_g, start_b = current["r"], current["g"], current["b"]
        else:
            start_r, start_g, start_b = 255, 255, 255

        steps = 20
        delay = duration / steps

        for i in range(steps + 1):
            factor = i / steps
            current_r = int(start_r * (1 - factor) + r * factor)
            current_g = int(start_g * (1 - factor) + g * factor)
            current_b = int(start_b * (1 - factor) + b * factor)
            self.set_color(current_r, current_g, current_b, temp=None)
            time.sleep(delay)

    def stop_effect(self, blocking=False):
        """Stop any running effect thread.

        Args:
            blocking: If True, wait for thread to finish. If False, signal and return immediately.
        """
        if self._effect_thread and self._effect_thread.is_alive():
            debug_print("Stopping current effect...")
            self._effect_stop_event.set()
            if blocking:
                self._effect_thread.join(timeout=0.5)
        self._effect_stop_event.clear()
        self._effect_thread = None

    def set_mode_color(self, r, g, b, period=3.0):
        """Set a solid color for the given mode.

        The H607C's firmware adds warm white when RGB values are scaled,
        causing visible flickering. This method sets the color once and
        maintains it reliably.

        Args:
            r, g, b: Target color (0-255)
            period: Unused, kept for API compatibility
        """
        if not self.isInitialized:
            debug_print("Cannot set color: device not initialized")
            return

        self.stop_effect()
        debug_print(f"Setting solid color RGB({r},{g},{b})")

        self.set_color(r, g, b, temp=None)
