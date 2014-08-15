import subprocess
import binascii
import hashlib
import struct


class Packet:
    def __init__(self, rid, payload):
        self.payload = payload
        self.rid = rid
        self.digest = self.sig = None

    def packets(self):
        r = [self.header_packet()]
        r.extend(self.data_packets())
        return r

    def header_packet(self):
        return struct.pack('> H i 12s 40s', self.rid, len(self.payload), self.digest()[:12], self.signature())

    # fragment payload into data packets
    def data_packets(self):
        ret = []
        c = 0
        while c < len(self.payload):
            pkt = self.payload[c:c + 56]
            while len(pkt) < 56:
                pkt += b"\x00"
            ret.append(struct.pack('> H 56s', self.rid, pkt))
            c += 56
        return ret

    def digest(self):
        if (self.digest):
            return self.digest
        sha1 = hashlib.sha1()
        sha1.update(struct.pack('> H', self.rid))
        sha1.update(self.payload)
        self.digest = sha1.digest()
        return self.digest

    def signature(self):
        if self.sig:
            return self.sig
        digesthex = binascii.hexlify(self.digest)
        p = subprocess.Popen(['./lib/signer', 'sign'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(digesthex)
        outlines = out.split("\n")
        result = outlines[1]
        self.sig = binascii.unhexlify(result)
        return self.sig
