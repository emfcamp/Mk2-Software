import tornado
import struct


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
        rid = 45057  # 0xB001
        open_window_msg = struct.pack('>L', self.duration)

        self.ctx.q.add_message(rid, open_window_msg)

        # As an information that the queue needs to be blocked for a certain time now
        duration_in_seconds = float(self.duration + self.ctx.config["additionalTransmitWindowTime"]) / 1000
        self.ctx.q.add_queue_pauser(duration_in_seconds)
