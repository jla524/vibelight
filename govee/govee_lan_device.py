import json
import time
from . import udp
from . import discover

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
            print(f"Discovered Govee LED device: {name} at {ip} ({mac})")

    def on(self):
        """Turn the light on."""
        payload = {"msg": {"cmd": "turn", "data": {"value": 1}}}
        print("Turning on...")
        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)

    def off(self):
        """Turn the light off."""
        payload = {"msg": {"cmd": "turn", "data": {"value": 0}}}
        print("Turning off...")
        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)

    def brightness(self, brightness):
        """Set brightness (0-100)."""
        brightness = max(0, min(100, int(brightness)))
        payload = {"msg": {"cmd": "brightness", "data": {"value": brightness}}}
        print(f"Setting brightness to {brightness}%...")
        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)

    def color(self, colors, temp=6500):
        """Set color and color temperature."""
        r = max(0, min(255, int(colors[0])))
        g = max(0, min(255, int(colors[1])))
        b = max(0, min(255, int(colors[2])))
        temp = max(2700, min(9000, int(temp)))

        payload = {
            "msg": {
                "cmd": "colorwc",
                "data": {"color": {"r": r, "g": g, "b": b}, "colorTemInKelvin": temp},
            }
        }
        print(f"Setting color to RGB({r},{g},{b}) @ {temp}K...")
        udp.send_udp_packet(self.ip, DEVICE_CONTROL_PORT, payload)

    # Convenience methods used by vibe.py
    def set_brightness(self, brightness):
        """Convenience method matching vibe.py expectations."""
        self.brightness(brightness)

    def set_color(self, r, g, b, temp=6500):
        """Convenience method matching vibe.py expectations.
        Default color temperature is 6500K (neutral daylight)."""
        self.color([r, g, b], temp)

    def blink(self, reps=1):
        """Blink the light."""
        current_state = self.status()
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

    def status(self):
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
