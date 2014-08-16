#!/usr/bin/env python
import json
import logging
import sys
import emfgateway
import socket
from uuid import getnode as get_mac

# Parse arguments
if len(sys.argv) < 3:
    print "Usage: ./app.py <hostname_to_connect_to> <3_character_identifier>"
    sys.exit(1)
hostname = sys.argv[1]
identifier = sys.argv[2]
if len(identifier) != 3:
    print "Identifier needs to be exactly 3 ASCII characters long"
    sys.exit(1)

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
    "identifier": identifier,
    "radios": usb_radios.getInformation(),
    "mac": mac
}
socket.send(json.dumps(initialInformation) + "\n")
logger.info("Established connection to mcp")

# Start gatway
gateway = emfgateway.Gateway(usb_radios, socket)
gateway.startTransmitter()

# Idle
while True:
    pass
