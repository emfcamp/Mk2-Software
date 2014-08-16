import json
import sys
import tornado
import binascii
import struct
from tornado.tcpserver import TCPServer
from tornado import gen


class McpTcpServer(TCPServer):

    def __init__(self, ctx):
        super(McpTcpServer, self).__init__()
        self.ctx = ctx
        self.connections = {}
        self.nextConnectionId = 0
        self.logger = ctx.get_logger().bind(origin='TcpServer')

    def send(self, connectionId, message):
        connection = self.connections[connectionId]
        if connection:
            connection['stream'].write(json.dumps(message) + "\n")
        else:
            self.logger.warn("Trying to send to connection that is already closed", cid=connectionId)

    def get_unused_channel(self):
        for channel in range(6, 200, 2):
            for connection in self.connections.itervalues():
                if connection['mainChannel'] == channel:
                    break
            else:
                return channel

    # gen.coroutine was swallowing errors since it's returning a future. This bubbles errors up.
    @gen.engine
    def handle_stream(self, stream, address):
        try:
            connectionId = self.nextConnectionId
            self.logger.info("handle_stream", connId=connectionId)
            self.nextConnectionId += 1
            ip = address[0]
            port = address[1]
            log = self.ctx.get_logger().bind(origin='tcpserver', cid=connectionId, ip=ip, port=port)
            log.info("socket_connected")

            # Initial packet
            line = yield stream.read_until('\n')
            gwInfo = json.loads(line)
            log.info("got_initial_info", gwinfo=gwInfo)

            # Check conditions
            numberOfRadios = gwInfo["numberOfRadios"]
            identifier = gwInfo["identifier"]
            if numberOfRadios < 2:
                log.warn("too_few_radios", num=numberOfRadios)
                stream.close()
                return
            if len(identifier) != 3:
                log.warn("invalid_identifier", id=identifier)
                stream.close()
                return

            # Find unused channel
            mainChannel = self.get_unused_channel()
            log.info("assigning_channel", channel=mainChannel)

            # Store connection away
            self.connections[connectionId] = {
                "connectionId": connectionId,
                "numberOfRadios": numberOfRadios,
                "identifier": identifier,
                "stream": stream,
                "logger": log,
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
                self.logger.info("msg_recvd", response=response.strip(), ip=ip)

        except tornado.iostream.StreamClosedError as e:
            self.connections[connectionId]['logger'].warn("connection_closed_error")
            self.remove_connection(connectionId)

        except BaseException as e:
            loggerForException = self.logger
            if connectionId in self.connections:
                loggerForException = self.connections[connectionId]['logger']
            loggerForException.error("connection_exception", info=sys.exc_info()[0], e=str(e))
            stream.close()
            self.remove_connection(connectionId)
            raise

    def remove_connection(self, connectionId):
        if connectionId in self.connections:
            self.ctx.q.delete_connection(connectionId)
            del self.connections[connectionId]
