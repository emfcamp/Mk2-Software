import tornado
import binascii


class MainChannelSender:
    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger().bind(origin='MainChannelSender')

    def start(self):
        delay = self.ctx.config["radioNormalPacketDelay"]
        self.logger.info("starting_normal_channel_timer", delay=delay)
        self.ioloop = tornado.ioloop.PeriodicCallback(self.tick, delay)
        self.ioloop.start()

    def tick(self):
        for connectionId, connection in self.ctx.tcpserver.connections.items():
            #self.logger.debug("tick", num_connections=(len(self.ctx.tcpserver.connections)))
            payload = self.ctx.q.get_next_packet(connectionId)
            if payload is not None:
                self.ctx.tcpserver.send(connectionId, {
                    "type": "send",
                    "radioId": 1,
                    "payload": binascii.hexlify(payload)
                })
