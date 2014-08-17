import json
import struct
import binascii


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
    RETURN_BADGE_ID = 0xB002


class Connection(object):
    """State object, one per TCP connection to a gateway"""

    def __init__(self, **args):
        #self.mac = args['mac']
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
            self.logger.warn('malformed_message', payload=payload)
            return  # broken packet or similar

        rid = struct.unpack('>H', payload[0:2])[0]
        sender_id = struct.unpack('>H', msg[2:4])[0]

        self.logger.info("msg_recvd",
                         msg=binascii.hexlify(payload),
                         rid=rid,
                         sender_id=sender_id,
                         )

        body = payload[4:]
        if rid == RID.IDENT:
            return self.handle_ident(sender_id, body)

        self.logger.warn("unhandled_msg_received", rid=rid, sender_id=sender_id)

    def handle_ident(self, sender_id, body):
        hwid = body[0:16]
        self.logger.info("badge_id_msg",
                         hwid=hwid,
                         sender_id=sender_id)

        badge = self.ctx.badgedb.register(hwid, self.cid, self.identifier)

        response = hwid + struct.pack('>H', badge['id'])
        self.ctx.q.add_message(self.cid, RID.RETURN_BADGE_ID, response)
