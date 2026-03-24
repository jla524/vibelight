import sys
import time
from datetime import datetime

import serial
from serial.tools import list_ports


def get_port():
    for p in list_ports.comports():
        if "usbmodem" in p.device or "Arduino" in str(p.description):
            return p.device
    return "/dev/cu.usbmodem2101"


PORT = get_port()

try:
    ser = serial.Serial(PORT, 9600, timeout=1)
    ser.dtr = False
    ser.rts = False
    time.sleep(2)
except Exception as error:
    sys.exit(1)


def send(status: str):
    cmd = f"{status.upper()}\n"
    ser.write(cmd.encode())
    time.sleep(0.1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        send(sys.argv[1])
    else:
        print("Usage: python opencode-led.py [plan|build|idle]")
