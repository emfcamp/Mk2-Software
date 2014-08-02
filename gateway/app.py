#!/usr/bin/env python
import os
import sys
import re
import subprocess
import socket
import json
import logging
import readlines

# parse arguments
if len(sys.argv) == 1:
    print "Please define the hostname of the mcp as the first argument"
    sys.exit(1)
mcpHostname = sys.argv[1]

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('main')

# Find all radio mount points
bashFoo = "ls /dev/ttyACM* | xargs -IPATH sh -c \"udevadm info --name=PATH | grep -q 'ID_MODEL_ID=16a6' && echo PATH\"; true"
serialDevices = subprocess.check_output(bashFoo, shell=True).strip().split('\n')
for serialPath in serialDevices:
    logger.info("Found USB radio: %s", serialPath)

# Connect to mcp
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((mcpHostname, 36000))
initialInformation = {"numberOfRadios": len(serialDevices)}
sock.send(json.dumps(initialInformation) + "\n")
logger.info("Established connection to mcp")

# Wait 
for line in readlines.readlines(sock):
    logger.info("Received packet: %s", line)


