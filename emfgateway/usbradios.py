import sys
import subprocess
import logging
import serial
import time
import re
import binascii

class MockUsbRadios:
    def __init__(self):
        self.logger = logging.getLogger('MockUsbRadios')

    def setup(self):
        pass

    def sendPacket(self, radio_id, packet):
        self.logger.info("sendPacket %d %s" % (radio_id, packet))
        pass

    def sendConfig(self, configurations):
        self.logger.info("sendConfig %r" % configurations)
        pass

    def getNumberOfRadios(self):
        return 2

    def getInformation(self):
        return []

    def readPacket(self, radio_id, length):
        return None

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
        if radio_id == 1:
            packet = packet.ljust(58, '\0')
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
                command = command.encode('ascii', 'ignore')
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
