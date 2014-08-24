import json
import sys
import tornado
import binascii
import struct
import traceback
from tornado.tcpserver import TCPServer
from tornado import gen
from .connection import Connection


class TcpServer(TCPServer):

    def __init__(self, ctx):
        super(TcpServer, self).__init__()
        self.ctx = ctx
        self.connections = {}
        self.logger = ctx.get_logger().bind(origin='TcpServer')

    def sendToAll(self, msgBuilderFun):
        numsent = 0
        for (cid, conn) in self.connections.items():
            m = msgBuilderFun(cid, conn)
            if m is not None:
                self.send(cid, m)
                numsent += 1
        return numsent

    def send(self, connectionId, message):
        connection = self.connections[connectionId]
        if connection:
            connection.stream.write(json.dumps(message) + "\n")
        else:
            self.logger.warn("Trying to send to connection that is already closed", cid=connectionId)

    def get_unused_channel(self):
        for channel in range(6, 200, 2):
            for connection in self.connections.itervalues():
                if connection.mainChannel == channel:
                    break
            else:
                return channel

    # gen.coroutine was swallowing errors since it's returning a future. This bubbles errors up.
    @gen.engine
    def handle_stream(self, stream, address):
        connectionId = None
        try:
            self.logger.info("handle_stream", connId=connectionId)
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
            if numberOfRadios < 2:
                log.warn("too_few_radios", num=numberOfRadios)
                stream.close()
                return

            # Find unused channel
            mainChannel = self.get_unused_channel()
            log.info("assigning_channel", channel=mainChannel)

            claimed_ip = gwInfo['ip']
            cur = self.ctx.cursor()
            cur.execute("SELECT id FROM gateway WHERE hwid = %s", (hex(gwInfo['mac']),))
            row = cur.fetchone()
            if row is None:
                cur.execute("INSERT INTO gateway(hwid) VALUES(%s) RETURNING id", (hex(gwInfo['mac']),))
                row = cur.fetchone()
                connectionId = row[0]
            else:
                connectionId = row[0]

            # our 3-char string id for a connection:
            identifier = connectionId
            #hex(connectionId)[-3:]

            connection = Connection(ctx=self.ctx,
                                    cid=connectionId,
                                    identifier=identifier,
                                    numberOfRadios=numberOfRadios,
                                    stream=stream,
                                    logger=self.logger,
                                    mainChannel=mainChannel,
                                    ip=claimed_ip,
                                    port=port,
                                    mac=hex(gwInfo['mac']),
                                    )
            # Store connection away
            self.connections[connectionId] = connection

            self.ctx.pub('gateway_connected',
                         sender="%s:%d" % (ip, port),
                         connectionId=connectionId,
                         )
            # friendly log for admin ui:
            self.ctx.note("New Gateway Connected, cid: %d " % (connectionId, ))

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
                connection.handle_message(response.strip())

        except tornado.iostream.StreamClosedError as e:
            self.connections[connectionId].logger.warn("connection_closed_error")
            self.remove_connection(connectionId)

        except BaseException as e:
            loggerForException = self.logger
            if connectionId in self.connections:
                loggerForException = self.connections[connectionId].logger
            loggerForException.error("connection_exception", info=sys.exc_info()[0], e=str(e), stacktrace=traceback.format_exc())
            stream.close()
            self.remove_connection(connectionId)
            raise

    def remove_connection(self, connectionId):
        if connectionId in self.connections:
            self.ctx.q.delete_connection(connectionId)
            del self.connections[connectionId]
            self.ctx.pub('gateway_disconnected',
                         connectionId=connectionId,
                         )
            self.ctx.note("Gateway Disconnected, cid: %d" % (connectionId))
