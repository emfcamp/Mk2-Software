import json
import sys
import tornado
import binascii
import struct
from tornado.tcpserver import TCPServer
from tornado import gen


class RID:
    UNIDENTIFIED = 0x0000
    ACK_RECEIVER = 0x9001
    IDENT = 0x9002
    PINGPONG = 0x9003
    BATTERY = 0x9004

    WEATHER = 0xA002
    SCHEDULE_FRI = 0xA003
    SCHEDULE_SAT = 0xA004
    SCHEDULE_SUN = 0xA005

    OPEN_TRANSMIT_WINDOW = 0xB001
    RETURN_BADGE_IDS = 0xB002


class Connection(object):
    """State object, one per TCP connection to a gateway"""

    def __init__(self, **args):
        self.mac = args['mac']
        self.ctx = args['ctx']
        self.cid = args['cid']
        self.numRadios = args['numberOfRadios']
        self.identifier = args['identifier']
        self.stream = args['stream']
        self.mainChannel = args['mainChannel']
        self.ip = args['ip']
        self.port = args['port']
        self.logger = args['logger'].bind(cid=self.cid,
                                          gw_addr="%s:%d" % (self.ip, self.port),
                                          identifier=self.identifier
                                          )

    def handle_message(self, msg):
        #self.ctx.pub('msg_recvd',
                        #sender="%s:%d" % (self.ip, self.port),
                        #connectionId=self.cid,
                        #)
        msg = json.loads(msg)
        payload = binascii.unhexlify(msg['payload'])

        if len(payload) < 4:
            return # broken packet or similar
        rid = struct.unpack('>H', payload[0:2])[0]

        self.logger.info("msg_recvd",
                         msg=binascii.hexlify(payload),
                         rid=rid
                         )

        body = msg[2:]
        if rid == RID.RETURN_BADGE_IDS:
            return self.handle_return_badge_ids(body)

        self.logger.warn("unhandled_msg_received", rid=rid)

    def handle_return_badge_ids(self, msg):
        sender_id = struct.unpack('>H', msg[0:2])
        unique_id = msg[2:18]
        self.logger.info("badge_id_msg", sender_id=sender_id, unique_id=unique_id)


class McpTcpServer(TCPServer):

    def __init__(self, ctx):
        super(McpTcpServer, self).__init__()
        self.ctx = ctx
        self.connections = {}
        self.nextConnectionId = 0
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

            connection = Connection(ctx=self.ctx,
                                    cid=connectionId,
                                    numberOfRadios=numberOfRadios,
                                    identifier=identifier,
                                    stream=stream,
                                    logger=self.logger,
                                    mainChannel=mainChannel,
                                    ip=ip,
                                    port=port,
                                    mac=gwInfo['mac'],
                                    )
            # Store connection away
            self.connections[connectionId] = connection

            self.ctx.pub('gateway_connected',
                         sender="%s:%d" % (ip, port),
                         connectionId=connectionId,
                         identifier=identifier,
                         )

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
            loggerForException.error("connection_exception", info=sys.exc_info()[0], e=str(e))
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
