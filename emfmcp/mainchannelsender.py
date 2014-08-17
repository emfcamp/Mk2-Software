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
        q = self.ctx.q

        def msgBuilder(cid, _conn):
            payload = q.get_next_packet(cid)
            if payload is None:
                return None
            else:
                return {
                    "type": "send",
                    "radioId": 1,
                    "payload": binascii.hexlify(payload)
                }

        self.ctx.tcpserver.sendToAll(msgBuilder)
