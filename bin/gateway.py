#!/usr/bin/env python
import json
import logging
import sys
import emfgateway
import socket
import Queue
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
initialInformation = {
    "type": "initial",
    "numberOfRadios": usb_radios.getNumberOfRadios(),
    "radios": usb_radios.getInformation(),
    "mac": mac,
    "identifier":"xxx" # ToDo: Remove this when the mcp doesn't need this anymore
}
socket.send(json.dumps(initialInformation) + "\n")
logger.info("Established connection to mcp")

# Shutdown queue
shutdownQueue = Queue.Queue()

# Start gatway
gateway = emfgateway.Gateway(usb_radios, socket, shutdownQueue)
gateway.startTransmitter()

# Wait until we get a shutdown signal
while True:
    try:
        shutdownMessage = shutdownQueue.get(True, 0.1)
        logger.warn("Received shutdown signal from thread: " + shutdownMessage)
        socket.close()
        sys.exit(1)
    except Queue.Empty:
        pass
