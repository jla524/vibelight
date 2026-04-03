import json
from . import udp
from .utils import debug_print

# Govee Multicast Network Parameters
MCAST_GRP = "239.255.255.250"
MCAST_SEND_PORT = 4001
MCAST_RECV_PORT = 4002

# Govee Multicast UDP Packet for discovery
discover_message = {"msg": {"cmd": "scan", "data": {"account_topic": "reserve"}}}


def discover_govee_leds(max_retries=2):
    """Discover Govee LED devices on the local network via multicast.

    Retries discovery on failure with exponential backoff.
    Returns (ip, mac, name) or (None, None, None) if not found.
    """
    for attempt in range(max_retries):
        try:
            success = udp.send_udp_packet(MCAST_GRP, MCAST_SEND_PORT, discover_message)
            if not success:
                debug_print(f"Discovery send failed on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    import time

                    time.sleep(0.2 * (attempt + 1))
                continue

            data, addr = udp.receive_udp_packet(MCAST_GRP, MCAST_RECV_PORT, 5)

            if data is None:
                debug_print(f"No response on discovery attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    import time

                    time.sleep(0.2 * (attempt + 1))
                continue

            try:
                discovery_data = json.loads(data.decode("utf-8"))
                ip = discovery_data["msg"]["data"]["ip"]
                mac = discovery_data["msg"]["data"]["device"]
                name = discovery_data["msg"]["data"]["sku"]
                debug_print(f"Discovered device: {name} at {ip} ({mac})")
                return ip, mac, name
            except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
                debug_print(f"Failed to parse discovery response: {e}")
                if attempt < max_retries - 1:
                    import time

                    time.sleep(0.2 * (attempt + 1))
                continue

        except Exception as e:
            debug_print(f"Discovery error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                import time

                time.sleep(0.2 * (attempt + 1))
            continue

    debug_print("No Govee LED devices found after all retries.")
    return None, None, None
