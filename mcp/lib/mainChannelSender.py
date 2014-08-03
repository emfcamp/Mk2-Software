import logging
import signal
import tornado
import struct
import binascii
import time
import unicodedata

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
        for connectionId, connection in self.mcpTcpServer.connections.items():
            payload = self.dataQueue.get_next_packet(connectionId)
            if payload != None:
                self.mcpTcpServer.send(connectionId, {
                    "type":"send",
                    "radioId": 1,
                    "payload": binascii.hexlify(payload)
                })
        

