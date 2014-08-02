import logging
import json
import sys
import tornado
from tornado.tcpserver import TCPServer
from tornado import gen

class McpTcpServer(TCPServer):
    
    def __init__(self, config):
        super(McpTcpServer, self).__init__()
        self.config = config
        self.connections = {}
        self.nextConnectionId = 0;
        self.logger = logging.getLogger('McpTcpServer')

    def send_to_all(self, message):
        for key in self.connections:
            send(key, message)

    def send(self, connectionId, message):
        connection = self.connections[connectionId]
        if connection:
            connection['stream'].write(json.dumps(message) + "\n")
        else:
            self.logger.warn("Trying to send to connection that is already closed: %d", connectionId)

    @gen.coroutine
    def handle_stream(self, stream, address):
        try:
            connectionId = self.nextConnectionId;
            self.nextConnectionId += 1
            ip = address[0]
            port = address[1]
            logger = logging.getLogger('socket-{0}@{1}:{2}'.format(connectionId, ip, port))
            logger.info("Connection opened")
        
            # Initial packet
            line = yield stream.read_until('\n')
            gwInfo = json.loads(line);
            logger.info("Received initial information: %s", gwInfo)

            # Check conditions
            numberOfRadios = gwInfo["numberOfRadios"]
            if numberOfRadios < 2:
                logger.warn("Too few radios. Ignoring connection.")
                return

            # Store connection away
            self.connections[connectionId] = {
                "connectionId": connectionId,
                "numberOfRadios": numberOfRadios,
                "stream": stream,
                "logger": logger
            }

            # Wait for incoming data
            while True:
                response = yield stream.read_until('\n')
                logger.info("Received: %s (%s)", response.strip(), ip)


        except tornado.iostream.StreamClosedError as e:
            self.connections[connectionId]['logger'].warn("Connection has been closed")
            del self.connections[connectionId]

        except Exception as e:
            self.connections[connectionId]['logger'].error("Unexpected exception found for connection %s: '%s' %s", ip, sys.exc_info()[0], e);
            stream.close()
            del self.connections[connectionId]
            raise
         

        