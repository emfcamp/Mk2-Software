import sys
import signal
from tornado.ioloop import IOLoop


class Main:
    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger().bind(origin='main')

    def handle_signal(self, sig, frame):
        IOLoop.instance().add_callback(IOLoop.instance().stop)
        self.logger.info("shutdown")

    def handle_exception(self):
        self.logger.error("unhandled_error", info=sys.exc_info()[0])

    def start(self):
        hostname = self.ctx.config['hostname']
        port = self.ctx.config['port']

        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        self.ctx.tcpserver.listen(port, hostname)
        self.logger.info("server_started", hostname=self.ctx.config['hostname'], port=self.ctx.config['port'])

        IOLoop.instance().start()
        IOLoop.instance().close()
