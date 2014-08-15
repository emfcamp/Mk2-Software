import logging
import signal
from tornado.ioloop import IOLoop

class Main:
    def __init__(self, config, mcpTcpServer):
        self.config = config
        self.mcpTcpServer = mcpTcpServer
        self.logger = logging.getLogger('main')

    def handle_signal(self, sig, frame):
        IOLoop.instance().add_callback(IOLoop.instance().stop)
        self.logger.info("Shutting down server now")

    def handle_exception(self):
        print "Unexpected error:", sys.exc_info()[0]

    def start(self):
        hostname = self.config['hostname']
        port = self.config['port']

        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        self.mcpTcpServer.listen(port, hostname)
        self.logger.info("Server started on %s:%d", self.config['hostname'], self.config['port'])

        IOLoop.instance().start()
        IOLoop.instance().close()

        

