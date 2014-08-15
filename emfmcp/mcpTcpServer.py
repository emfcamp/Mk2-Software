import logging
import json
import sys
import tornado
import binascii
import struct
from tornado.tcpserver import TCPServer
from tornado import gen


class McpTcpServer(TCPServer):

    def __init__(self, config, dataQueue):
        super(McpTcpServer, self).__init__()
        self.config = config
        self.dataQueue = dataQueue
        self.connections = {}
        self.nextConnectionId = 0
        self.logger = logging.getLogger('McpTcpServer')

    def send(self, connectionId, message):
        connection = self.connections[connectionId]
        if connection:
            connection['stream'].write(json.dumps(message) + "\n")
        else:
            self.logger.warn("Trying to send to connection that is already closed: %d", connectionId)

    def get_unused_channel(self):
        for channel in range(6, 200, 2):
            for connection in self.connections:
                if connection['mainChannel'] == channel:
                    break
            else:
                return channel

    # gen.coroutine was swallowing errors since it's returning a future. This bubbles errors up.
    @gen.engine
    def handle_stream(self, stream, address):
        try:
            connectionId = self.nextConnectionId
            self.nextConnectionId += 1
            ip = address[0]
            port = address[1]
            logger = logging.getLogger('socket-{0}@{1}:{2}'.format(connectionId, ip, port))
            logger.info("Connection opened")

            # Initial packet
            line = yield stream.read_until('\n')
            gwInfo = json.loads(line)
            logger.info("Received initial information: %s", gwInfo)

            # Check conditions
            numberOfRadios = gwInfo["numberOfRadios"]
            identifier = gwInfo["identifier"]
            if numberOfRadios < 2:
                logger.warn("Too few radios (%d). Closing connection.", numberOfRadios)
                stream.close()
                return
            if len(identifier) != 3:
                logger.warn("Invalid identifier: %s. Closing connection.", identifier)
                stream.close()
                return

            # Find unused channel
            logger.info("Find channel...")
            mainChannel = self.get_unused_channel()
            logger.info("Assigning channel 0x%s",  binascii.hexlify(struct.pack("B", mainChannel)))

            # Store connection away
            self.connections[connectionId] = {
                "connectionId": connectionId,
                "numberOfRadios": numberOfRadios,
                "identifier": identifier,
                "stream": stream,
                "logger": logger,
                "mainChannel": mainChannel
            }

            # Configure radios
            self.send(connectionId, {
                "type": "configure",
                "configurations": [
                    ["ATPK08", "ATCN02", "ATAC", "ATDN"],
                    ["ATPK3A", "ATCN" + binascii.hexlify(struct.pack("B", mainChannel)), "ATAC", "ATDN"]
                ]
            })

            # Wait for incoming data
            while True:
                response = yield stream.read_until('\n')
                logger.info("Received: %s (%s)", response.strip(), ip)

        except tornado.iostream.StreamClosedError as e:
            self.connections[connectionId]['logger'].warn("Connection has been closed")
            self.remove_connection(connectionId)

        except BaseException as e:
            loggerForException = self.logger
            if connectionId in self.connections:
                loggerForException = self.connections[connectionId]['logger']
            loggerForException.error("Unexpected exception found for connection %s: '%s' %s", ip, sys.exc_info()[0], e)
            stream.close()
            self.remove_connection(connectionId)
            raise

    def remove_connection(self, connectionId):
        if connectionId in self.connections:
            self.dataQueue.delete_connection(connectionId)
            del self.connections[connectionId]
