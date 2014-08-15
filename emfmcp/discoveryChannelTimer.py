import logging
import tornado
import struct
import binascii
import time


class DiscoveryChannelTimer:
    def __init__(self, config, mcpTcpServer):
        self.config = config
        self.mcpTcpServer = mcpTcpServer
        self.connectionIndex = 0
        self.logger = logging.getLogger('discoveryChannelTimer')

    def start(self):
        delay = self.config["radioDiscoveryPacketDelay"]
        self.logger.info("Starting discovery channel timer with delay %dms", delay)
        self.ioloop = tornado.ioloop.PeriodicCallback(self.tick, delay)
        self.ioloop.start()

    def tick(self):
        if len(self.mcpTcpServer.connections) > 0:
            self.connectionIndex = (self.connectionIndex + 1) % len(self.mcpTcpServer.connections)
            connectionIds = self.mcpTcpServer.connections.keys()
            connectionId = connectionIds[self.connectionIndex]
            connection = self.mcpTcpServer.connections[connectionId]

            mainChannel = connection["mainChannel"]
            timestamp = time.time()
            identifier = connection["identifier"].encode('ascii', 'replace')

            payload = struct.pack('> B I 3s', mainChannel, timestamp, identifier)

            self.mcpTcpServer.send(connectionId, {
                "type": "send",
                "radioId": 0,
                "payload": binascii.hexlify(payload)
            })
