#!/usr/bin/env python
import os
import sys
import re
import subprocess
import socket
import json
import logging
import readlines
import serial 
import time
import binascii

# parse arguments
if len(sys.argv) < 3:
    print "Usage: ./app.py <hostname_to_connect_to> <3_character_identifier>"
    sys.exit(1)
mcpHostname = sys.argv[1]
identifier = sys.argv[2]
if len(identifier) != 3:
    print "Identifier needs to be exactly 3 ASCII characters long"
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('main')

# Find all radio mount points
bashFoo = "ls /dev/ttyACM* | xargs -IPATH sh -c \"udevadm info --name=PATH | grep -q 'ID_MODEL_ID=16a6' && echo PATH\"; true"
serialDevices = subprocess.check_output(bashFoo, shell=True).strip().split('\n')

# Connect via serial and fetch information
radioInformation = []
serialConnections = []
packetsSend = []
for serialPath in serialDevices:
    logger.info("Found USB radio: %s", serialPath)
    serialConnections.append(serial.Serial(serialPath, 115200, timeout=0.1))
    radioInformation.append({"path": serialPath})
    packetsSend.append(0)
logger.info("Entering AT mode...")
for serialConnection in serialConnections:
    serialConnection.write("+++")
    serialConnection.flush()
time.sleep(1.1) # Wait before we send additional command
for i, information in enumerate(radioInformation):
    logger.info("Reading information for %s", information['path'])
    serialConnection = serialConnections[i]
    line = serialConnection.read(3).strip();
    if line != 'OK':
        logger.error("Couldn't enter AT mode on radio %s, got %s", information['path'], line)
        sys.exit(1)
    serialConnection.write("ATVR\r\n")
    serialConnection.flush()
    information['firmware'] = serialConnection.readline().split("\r")[0]
    logger.info("Firmware: %s", information['firmware'])
    serialConnection.write("ATDN\r\n")
    serialConnection.flush()

# Connect to mcp
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((mcpHostname, 36000))
initialInformation = {
    "type": "initial",
    "numberOfRadios": len(serialDevices),
    "identifier": identifier,
    "radios": radioInformation
}
sock.send(json.dumps(initialInformation) + "\n")
logger.info("Established connection to mcp")

# Loop forever 
for line in readlines.readlines(sock):
    #try:
    packet = json.loads(line)


    if packet["type"] == 'configure':
        configurations = packet["configurations"]
        time.sleep(1.1) # Wait before we enter AT mode
        for radioId, configuration in enumerate(configurations):
            logger.info("Configuring radio %d with %s", radioId, configuration)
            serialConnection = serialConnections[radioId]
            serialConnection.write("+++")
            serialConnection.flush()
        time.sleep(1.1) # Wait before we send commands
        for radioId, configuration in enumerate(configurations):
            serialConnection = serialConnections[radioId]
            line = serialConnection.read(3).strip();
            if line != 'OK':
                logger.error("Couldn't enter AT mode on radio %s, got %s", information['path'], line)
                sys.exit(1)
            for command in configuration:
                serialConnection.write(command + "\r\n")
                serialConnection.flush()
                line = serialConnection.readline().split("\r")[0]
                logger.info("Applied command '%s' to radio %d, got '%s'", command, radioId, line)

    elif packet["type"] == 'send':
        radioId = packet["radioId"]
        payload = binascii.unhexlify(packet["payload"])
        serialConnection = serialConnections[radioId]
        serialConnection.write(payload)
        serialConnection.flush()
        packetsSend[radioId] += 1
        logger.debug("Send packet on radio %d: %s", radioId, packet["payload"])
        if packetsSend[radioId] % 100 == 0:
            logger.debug("Packet send via radio %d: %s", radioId, packetsSend[radioId])
    else:
        logger.warn("Received invalid packet: %s", packet)
    #except Exception as e:
    #    logger.error("Unexpected exception found: '%s' %s", sys.exc_info()[0], e);
            


