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

# Retry settings for busy device
DEVICE_BUSY_RETRY_DELAY = 0.1  # 100ms initial delay
MAX_DEVICE_RETRIES = 3


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

                # Send failed, wait and retry
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

    def _send_command_fast(self, payload):
        """Send a single UDP packet without retry — for high-frequency effects."""
        if not self.isInitialized or not self.ip:
            return False
        try:
            return udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload, retries=1)
        except Exception:
            return False

    def is_responsive(self, timeout=2):
        """Check if device is responsive by sending a status request.

        Returns True if device responds, False otherwise.
        """
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

        self._send_command(payload)

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
            # Device responds via multicast, so we listen on multicast group
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

    def stop(self):
        """Stop any currently running effect."""
        if self._current_effect and self._current_effect.is_alive():
            self._stop_event.set()
            self._current_effect.join(timeout=1.0)
            self._current_effect = None
            self._stop_event.clear()
        debug_print("Stopped current effect.")

    def _breathe_thread(self, color, min_bright, max_bright, speed):
        """Background thread for breathing effect with natural easing.

        Brightness is baked into the RGB values (scaled by brightness/100) so
        that a single colorwc packet per tick controls both color and intensity.
        This avoids the two-command race where a separate brightness command is
        dropped or ignored by the H607C after a colorwc command.

        Uses a cosine curve with gamma correction for smooth, natural-looking
        transitions that match human brightness perception.
        """
        r, g, b = color
        phase = 0.0
        consecutive_failures = 0
        max_consecutive_failures = 10

        # Asymmetric breathing: faster inhale, slower exhale
        inhale_ratio = 0.4  # inhale takes 40% of the cycle

        # Gamma correction factor (standard sRGB gamma ~2.2)
        gamma = 2.2

        while not self._stop_event.is_set():
            try:
                # Normalized phase position within one full cycle (0 to 1)
                cycle_pos = (phase % (2 * math.pi)) / (2 * math.pi)

                # Asymmetric phase: warp the cycle so inhale is faster
                if cycle_pos < inhale_ratio:
                    # Inhale phase: map [0, inhale_ratio] -> [0, 0.5]
                    t = cycle_pos / inhale_ratio * 0.5
                else:
                    # Exhale phase: map [inhale_ratio, 1] -> [0.5, 1.0]
                    t = 0.5 + (cycle_pos - inhale_ratio) / (1 - inhale_ratio) * 0.5

                # Cosine easing: smooth at extremes, faster through midpoint
                eased = (1 - math.cos(t * 2 * math.pi)) / 2

                # Apply gamma correction for perceptual linearity
                gamma_eased = math.pow(eased, gamma)

                # Map to brightness range
                brightness = min_bright + (max_bright - min_bright) * gamma_eased
                factor = brightness / 100.0

                # Scale RGB by brightness factor and send as a single colorwc packet
                scaled_r = max(1, int(round(r * factor)))
                scaled_g = max(1, int(round(g * factor)))
                scaled_b = max(1, int(round(b * factor)))

                payload = {
                    "msg": {
                        "cmd": "colorwc",
                        "data": {
                            "color": {"r": scaled_r, "g": scaled_g, "b": scaled_b},
                            "colorTemInKelvin": 0,
                        },
                    }
                }
                success = self._send_command_fast(payload)
                if success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1

                if consecutive_failures >= max_consecutive_failures:
                    debug_print(
                        f"Too many consecutive failures ({max_consecutive_failures}), stopping breathe effect"
                    )
                    break

                phase += 0.08 * speed
                time.sleep(0.08)  # ~12 updates per second for smooth breathing
            except Exception as e:
                debug_print(f"Error in breathe thread: {e}")
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    debug_print(
                        f"Too many consecutive failures ({max_consecutive_failures}), stopping breathe effect"
                    )
                    break
                time.sleep(0.1)  # Brief pause on error

    def breathe(self, r, g, b, min_bright=20, max_bright=85, speed=2.0):
        """Start breathing effect with given color and parameters."""
        if not self.isInitialized:
            debug_print("Device not initialized.")
            return

        # Stop any existing effect
        self.stop()

        # Turn on unconditionally (idempotent - no harm if already on)
        self.on()
        time.sleep(0.15)

        # Set initial color (brightness is baked into RGB in the breathe thread)
        self.set_color(r, g, b, temp=None)
        time.sleep(0.1)

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
        """Smooth fade to a target color over specified duration with error handling."""
        if not self.isInitialized:
            return

        # Get current color to fade from
        current = self.get_status()
        if current:
            start_r, start_g, start_b = current["r"], current["g"], current["b"]
        else:
            start_r, start_g, start_b = 255, 255, 255

        steps = 20
        delay = duration / steps

        for i in range(steps + 1):
            if self._stop_event.is_set():
                break
            factor = i / steps
            current_r = int(start_r * (1 - factor) + r * factor)
            current_g = int(start_g * (1 - factor) + g * factor)
            current_b = int(start_b * (1 - factor) + b * factor)
            self.set_color(current_r, current_g, current_b, temp=None)
            time.sleep(delay)
