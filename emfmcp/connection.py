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
        self.identifier = args['identifier']
        self.numRadios = args['numberOfRadios']
        self.stream = args['stream']
        self.mainChannel = args['mainChannel']
        self.ip = args['ip']
        self.mac = args['mac']
        self.port = args['port']
        self.logger = args['logger'].bind(cid=self.cid, mac=self.mac,
                                          gw_addr="%s:%d" % (self.ip, self.port),
                                          )

        # A connection that has recently asked badges to transmit should not be transmitting itself
        self.pause_until = 0

        # Make sure our data q exists asap, so it's listed in api
        self.ctx.q.id2q(self.cid)

    def toJSON(self):
        return {'id': self.cid,
                'numRadios': self.numRadios,
                'mainChannel': self.mainChannel,
                'identifier': self.identifier,
                'ip': self.ip,
                'port': self.port,
                }

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

        rid, sender_id = struct.unpack('>H H', payload[0:4])

        self.logger.info("msg_recvd",
                         msg=binascii.hexlify(payload),
                         rid=rid,
                         sender_id=sender_id,
                         )

        body = payload[4:]
        if rid == RID.IDENT:
            return self.handle_ident(sender_id, body)

        self.logger.warn("unhandled_msg_received", rid=rid, sender_id=sender_id, msg=msg)

    def handle_ident(self, sender_id, body):
        hwid_raw = body[0:16]
        hwid = binascii.hexlify(hwid_raw)
        self.logger.info("badge_id_msg",
                         hwid=hwid,
                         sender_id=sender_id)

        badge = self.ctx.badgedb.register(hwid, self.cid, self.identifier)

        names = badge.getUserNames(self.ctx.cursor());
        name1 = names[0].encode('ascii', 'replace').ljust(10, '\0');
        name2 = names[1].encode('ascii', 'replace').ljust(10, '\0');

        response = hwid_raw + struct.pack('>H', badge.id) + name1 + name2
        self.ctx.q.add_message_on_cid(self.cid, RID.RETURN_BADGE_ID, response)
