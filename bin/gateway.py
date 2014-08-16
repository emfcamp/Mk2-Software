#!/usr/bin/env python
import json
import logging
import sys
import emfgateway
import socket
from uuid import getnode as get_mac

# Parse arguments
if len(sys.argv) == 2:
    hostname = sys.argv[1]
else:
    hostname = "localhost" # ToDo: replace with real hostname

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('main')

# Find and connect to radios
#usb_radios = emfgateway.MockUsbRadios()
usb_radios = emfgateway.UsbRadios()
usb_radios.setup()

# Get MAC ID
mac = get_mac()
logger.info("MAC: %s", mac);

# Connect to mcp
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((hostname, 36000))
socket.settimeout(3.0)
initialInformation = {
    "type": "initial",
    "numberOfRadios": usb_radios.getNumberOfRadios(),
    "radios": usb_radios.getInformation(),
    "mac": mac,
    "identifier":"xxx" # ToDo: Remove this when the mcp doesn't need this anymore
}
socket.send(json.dumps(initialInformation) + "\n")
logger.info("Established connection to mcp")

# Start gatway
gateway = emfgateway.Gateway(usb_radios, socket)
gateway.startTransmitter()

# Idle
while True:
    pass
