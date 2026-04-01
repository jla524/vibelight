import socket
import struct
import json


def send_udp_packet(ip, port, payload):
    """Send UDP packet (used for both multicast discovery and device control)."""
    packet = json.dumps(payload).encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    try:
        sock.sendto(packet, (ip, port))
    finally:
        sock.close()


def receive_udp_packet(ip, port, timeout=5):
    """Receive UDP packet with timeout."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.bind(("", port))
    sock.settimeout(timeout)

    try:
        data, addr = sock.recvfrom(1024)
        return data, addr
    except socket.timeout:
        return None, None
    finally:
        sock.close()
