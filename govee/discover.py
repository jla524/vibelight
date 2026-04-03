import json
from . import udp
from .utils import debug_print

# Govee Multicast Network Parameters
MCAST_GRP = "239.255.255.250"
MCAST_SEND_PORT = 4001
MCAST_RECV_PORT = 4002

# Govee Multicast UDP Packet for discovery
discover_message = {"msg": {"cmd": "scan", "data": {"account_topic": "reserve"}}}


def discover_govee_leds():
    """Discover Govee LED devices on the local network via multicast."""
    udp.send_udp_packet(MCAST_GRP, MCAST_SEND_PORT, discover_message)
    data, addr = udp.receive_udp_packet(MCAST_GRP, MCAST_RECV_PORT, 5)

    if data is None:
        debug_print("No Govee LED devices found on the network.")
        return None, None, None
    else:
        debug_print(f"Received message from {addr}: {data}")
        discovery_data = json.loads(data.decode("utf-8"))
        ip = discovery_data["msg"]["data"]["ip"]
        mac = discovery_data["msg"]["data"]["device"]
        name = discovery_data["msg"]["data"]["sku"]
        return ip, mac, name
