import tornado
import struct
import binascii


class TransmitWindowAnnouncer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger().bind(origin='TransmitWindowAnnouncer')

    def start(self):
        self.delay = self.ctx.config["transmitWindowInterval"]
        self.duration = self.ctx.config["transmitWindowDuration"]
        self.logger.info("starting_transmit_announcer", delay=self.delay, duration=self.duration)
        self.ioloop = tornado.ioloop.PeriodicCallback(self.tick, self.delay)
        self.ioloop.start()

    def tick(self):
        num_connections = len(self.ctx.tcpserver.connections)
        if num_connections == 0:
            return

        # TODO format of "open transmission window" message here:
        rid = 45057 #0xB001
        open_window_msg = struct.pack('>L', self.duration)

        #def msgBuilder(_cid, _conn):
        #    return {
        #        "type": "send",
        #        "radioId": 1,
        #        "payload": binascii.hexlify(open_window_msg)
        #    }

        #self.ctx.tcpserver.sendToAll(msgBuilder)

        #for (cid, conn) in self.ctx.tcpserver.connections.items():
        self.ctx.q.add_message(rid, open_window_msg)
