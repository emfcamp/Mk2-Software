import logging
import tornado
import binascii


class MainChannelSender:
    def __init__(self, config, mcpTcpServer, dataQueue):
        self.config = config
        self.mcpTcpServer = mcpTcpServer
        self.dataQueue = dataQueue
        self.logger = logging.getLogger('discoveryChannelTimer')

    def start(self):
        delay = self.config["radioNormalPacketDelay"]
        self.logger.info("Starting normal channel timer with delay %dms", delay)
        self.ioloop = tornado.ioloop.PeriodicCallback(self.tick, delay)
        self.ioloop.start()

    def tick(self):
        #self.logger.info("Main sending tick, %d connected clients" % (len(self.mcpTcpServer.connections)))
        for connectionId, connection in self.mcpTcpServer.connections.items():
            payload = self.dataQueue.get_next_packet(connectionId)
            if payload is not None:
                self.mcpTcpServer.send(connectionId, {
                    "type": "send",
                    "radioId": 1,
                    "payload": binascii.hexlify(payload)
                })
