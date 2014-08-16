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
import threading
from uuid import getnode as get_mac

class UsbRadios:
    def __init__(self):
        self.logger = logging.getLogger('UsbRadios')

    def setup(self):
        # Find all radio mount points
        bashFoo = "ls /dev/ttyACM* | xargs -IPATH sh -c \"udevadm info --query=all --name=PATH | grep -q 'ID_MODEL_ID=16a6' && echo PATH\"; true"
        self.serial_devices = subprocess.check_output(bashFoo, shell=True).strip().split('\n')

        # Regex that matches a packet
        self.packet_regex = re.compile('.{1,58}|-\d{3}')

        # Connect via serial
        self.radio_information = []
        self.serial_connections = []
        self.packets_send = []
        for serialPath in self.serial_devices:
            self.logger.info("Found USB radio: %s", serialPath)
            self.serial_connections.append(serial.Serial(serialPath, 115200, timeout=0.1))
            self.radio_information.append({"path": serialPath})
            self.packets_send.append(0)

        # Collect information about the radios
        self.logger.info("Entering AT mode...")
        for radio_id, information in enumerate(self.radio_information):
            self._send(radio_id, "+++")

        time.sleep(1.1) # Wait before we send additional command
        for radio_id, information in enumerate(self.radio_information):
            self._flushInput(radio_id)
            self._send(radio_id, "AT\r\n")
            result = self._readLine(radio_id)
            if result != 'OK':
                self.logger.error("Couldn't enter AT mode on radio %s, got %s", information['path'], result)
                result = self._readLine(radio_id)
                sys.exit(1)
            self.logger.info("Reading information for %s", information['path'])
            self._send(radio_id, "ATZD3\r\n")
            self._readLine(radio_id)
            self._send(radio_id, "ATVR\r\n")
            information['firmware'] = self._readLine(radio_id)
            self.logger.info("Firmware: %s", information['firmware'])
            self._send(radio_id, "ATDN\r\n")

    def sendPacket(self, radio_id, packet):
        self._send(radio_id, packet)
        self.packets_send[radio_id] += 1
        if self.packets_send[radio_id] % 100 == 0:
            self.logger.debug("Packet send via radio %d: %s", radio_id, self.packets_send[radio_id])

    def sendConfig(self, configurations):
        time.sleep(1.1) # Wait before we enter AT mode
        for radio_id, configuration in enumerate(configurations):
            self.logger.info("Configuring radio %d with %s", radio_id, configuration)
            self._send(radio_id, "+++")
        time.sleep(1.1) # Wait before we send commands
        for radio_id, configuration in enumerate(configurations):
            self._flushInput(radio_id)
            self._send(radio_id, "AT\r\n")
            result = self._readLine(radio_id)
            if result != 'OK':
                self.logger.error("Couldn't enter AT mode on radio %d, got %s", radio_id, result)
                raise Exception()
            for command in configuration:
                self._send(radio_id, command + "\r\n")
                result = self._readLine(radio_id)
                self.logger.info("Applied command '%s' to radio %d, got '%s'", command, radio_id, result)


    def _flushInput(self, radio_id):
        serial_connection = self.serial_connections[radio_id]
        serial_connection.flushInput()

    def _send(self, radio_id, content):
        serial_connection = self.serial_connections[radio_id]
        serial_connection.write(content)
        serial_connection.flush()

    def _readLine(self, radio_id):
        lineWithLinebreak = self.serial_connections[radio_id].readline()
        line = lineWithLinebreak.split("\r")[0]
        return line

    def getNumberOfRadios(self):
        return len(self.serial_connections)

    def getInformation(self):
        return self.radio_information

    def readPacket(self, radio_id, length):
        serial_connection = self.serial_connections[radio_id]
        data = b"";
        while not self.packet_regex.match(data):
            data = data + serial_connection.read(1)
            n = serial_connection.inWaiting()
            if n + len(data) > length:
                n = length - len(data)
            if n:
                data = data + serial_connection.read(n)
        return data


class Gateway:
    def __init__(self, aUsbRadios, aSocket):
        self.usb_radios = aUsbRadios
        self.socket = aSocket
        self.logger = logging.getLogger('Gateway')

    def receiver(self):
        try:
            self.logger.info("Receiver started")
            while True:
                packet = self.usb_radios.readPacket(1, 58)
                rssi = int(packet[-4:])
                packet = packet[:-5]
                self.logger.debug("Received packet with rssi %d: %s", rssi, packet)
                message = {
                    "type": "received",
                    "radioId": 1,
                    "payload": binascii.hexlify(packet),
                    "rssi": rssi
                }
                socket.send(json.dumps(message) + "\n")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.error("Unexpected exception found in receiver: %s %s %s", exc_type, exc_value, exc_traceback);
            self.socket.close()
            sys.exit(1)

    def transmitter(self):
        try:
            self.logger.info("Transmitter started")
            for line in readlines.readlines(self.socket):
                packet = json.loads(line)
                if packet["type"] == 'configure':
                    usb_radios.sendConfig(packet["configurations"])
                    # Only start the receive after the configuration packet has been send
                    self.startReceiver()
                elif packet["type"] == 'send':
                    payload = binascii.unhexlify(packet["payload"])
                    usb_radios.sendPacket(packet["radioId"], payload)
                else:
                    logger.warn("Received invalid packet: %s", packet)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.error("Unexpected exception found in transmitter: %s %s %s", exc_type, exc_value, exc_traceback);
            self.socket.close()
            sys.exit(1)

    def startReceiver(self):
        self.thread_receiver = threading.Thread(target=self.receiver)
        self.thread_receiver.setDaemon(True)
        self.thread_receiver.setName('reveiver')
        self.thread_receiver.start()

    def startTransmitter(self):
        self.thread_transmitter = threading.Thread(target=self.transmitter)
        self.thread_transmitter.setDaemon(True)
        self.thread_transmitter.setName('transmitter')
        self.thread_transmitter.start()

    def stop(self):
        self.log.debug('stopping')

if __name__ == '__main__':
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
    usb_radios = UsbRadios()
    usb_radios.setup();

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
    gateway = Gateway(usb_radios, socket);
    gateway.startTransmitter()

    # Idle
    while True:
        pass
