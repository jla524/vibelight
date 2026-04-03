import socket
import struct
import json
import time
from .utils import debug_print

# Govee Multicast Network Parameters
MCAST_GRP = "239.255.255.250"
MCAST_SEND_PORT = 4001
MCAST_RECV_PORT = 4002

MAX_RETRIES = 3
RETRY_DELAY_BASE = 0.1  # Start with 100ms, doubles each retry


def send_udp_packet(ip, port, payload, retries=MAX_RETRIES):
    """Send UDP packet with retry logic for transient failures.

    Retries on socket errors with exponential backoff.
    Returns True on success, False on failure (after all retries).
    """
    packet = json.dumps(payload).encode("utf-8")

    for attempt in range(retries):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(2.0)  # 2 second timeout per attempt
            sock.sendto(packet, (ip, port))
            return True
        except (socket.error, OSError) as e:
            delay = RETRY_DELAY_BASE * (2**attempt)
            debug_print(f"UDP send failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                debug_print(f"Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                debug_print(f"UDP send failed after {retries} attempts")
                return False
        finally:
            if sock:
                sock.close()

    return False


def receive_udp_packet(ip, port, timeout=5, retries=MAX_RETRIES):
    """Receive UDP packet with retry logic for transient failures.

    Retries on socket errors with exponential backoff.
    Returns (data, addr) on success, (None, None) on failure.
    """
    for attempt in range(retries):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.bind(("", port))
            sock.settimeout(timeout)

            data, addr = sock.recvfrom(1024)
            return data, addr
        except socket.timeout:
            # Timeout is expected for discovery, no retry needed
            return None, None
        except (socket.error, OSError) as e:
            delay = RETRY_DELAY_BASE * (2**attempt)
            debug_print(f"UDP receive failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                debug_print(f"Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                debug_print(f"UDP receive failed after {retries} attempts")
                return None, None
        finally:
            if sock:
                sock.close()

    return None, None


def send_and_receive_udp_packet(
    ip, port, payload, timeout=3, retries=MAX_RETRIES, multicast=False
):
    """Send UDP packet and wait for response on the same socket.

    The device responds via multicast group, so we must join the group
    to receive responses. Uses a single socket for both send and receive.
    Returns (data, addr) on success, (None, None) on failure.
    """
    packet = json.dumps(payload).encode("utf-8")

    for attempt in range(retries):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if multicast:
                mreq = struct.pack(
                    "4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY
                )
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                sock.bind(("", port))
            sock.settimeout(timeout)
            sock.sendto(packet, (ip, port))

            data, addr = sock.recvfrom(1024)
            return data, addr
        except socket.timeout:
            return None, None
        except (socket.error, OSError) as e:
            delay = RETRY_DELAY_BASE * (2**attempt)
            debug_print(
                f"UDP send/receive failed (attempt {attempt + 1}/{retries}): {e}"
            )
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None, None
        finally:
            if sock:
                sock.close()

    return None, None
