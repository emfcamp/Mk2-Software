import sys
import socket
import json
import logging
import readlines
import binascii
import threading


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
                if packet is None:
                    self.logger.info("Got None from radio.readPacket, stopping receiver")
                    return
                message = {
                    "type": "received",
                    "radioId": 1,
                    "payload": binascii.hexlify(packet),
                    "rssi": "not_done_yet"
                }
                socket.send(json.dumps(message) + "\n")
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.error("Unexpected exception found in receiver: %s %s %s", exc_type, exc_value, exc_traceback)
            self.socket.close()
            sys.exit(1)

    def transmitter(self):
        try:
            self.logger.info("Transmitter started")
            for line in readlines.readlines(self.socket):
                packet = json.loads(line)
                self.logger.info("transmitter doing: %r" % packet)
                if packet["type"] == 'configure':
                    self.usb_radios.sendConfig(packet["configurations"])
                    # Only start the receive after the configuration packet has been send
                    self.startReceiver()
                elif packet["type"] == 'send':
                    payload = binascii.unhexlify(packet["payload"])
                    self.usb_radios.sendPacket(packet["radioId"], payload)
                else:
                    self.logger.warn("Received invalid packet: %s", packet)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.logger.error("Unexpected exception found in transmitter: %s %s %s", exc_type, exc_value, exc_traceback)
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
