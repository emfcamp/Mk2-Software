import tornado
import struct
import binascii
import time


class DiscoveryAnnouncer:
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

        def msgBuilder(connectionId, connection):
            identifier = connection.identifier.encode('ascii', 'replace')
            payload = struct.pack('> B I 3s',
                                  connection.mainChannel,
                                  time.time(),
                                  identifier
                                  )
            return {
                "type": "send",
                "radioId": 0,
                "payload": binascii.hexlify(payload)
            }

        self.ctx.tcpserver.sendToAll(msgBuilder)
