import tornado
import binascii
import time


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
            if _conn.pause_until < time.time():
                payload = q.get_next_packet(cid)
                if payload is None:
                    return None
                elif isinstance(payload, float):
                    duration_in_seconds = payload
                    _conn.pause_until = time.time() + duration_in_seconds
                    self.logger.info("pause_connection_for_duration", pause_until=_conn.pause_until)
                else:
                    print binascii.hexlify(payload)
                    return {
                        "type": "send",
                        "radioId": 1,
                        "payload": binascii.hexlify(payload)
                    }

        self.ctx.tcpserver.sendToAll(msgBuilder)
