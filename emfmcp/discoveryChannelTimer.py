import tornado
import struct
import binascii
import time


class DiscoveryChannelTimer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.connectionIndex = 0
        self.logger = ctx.get_logger().bind(origin='discoveryChannelTimer')

    def start(self):
        delay = self.ctx.config["radioDiscoveryPacketDelay"]
        self.logger.info("starting_discovery_channel_timer", delay=delay)
        self.ioloop = tornado.ioloop.PeriodicCallback(self.tick, delay)
        self.ioloop.start()

    def tick(self):
        num_connections = len(self.ctx.tcpserver.connections)
        if num_connections > 0:
            #self.logger.debug("tick", num_connections=num_connections)
            self.connectionIndex = (self.connectionIndex + 1) % len(self.ctx.tcpserver.connections)
            connectionIds = self.ctx.tcpserver.connections.keys()
            connectionId = connectionIds[self.connectionIndex]
            connection = self.ctx.tcpserver.connections[connectionId]

            mainChannel = connection["mainChannel"]
            timestamp = time.time()
            identifier = connection["identifier"].encode('ascii', 'replace')

            payload = struct.pack('> B I 3s', mainChannel, timestamp, identifier)

            self.ctx.tcpserver.send(connectionId, {
                "type": "send",
                "radioId": 0,
                "payload": binascii.hexlify(payload)
            })
