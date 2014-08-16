import subprocess
import binascii
import hashlib
import struct


class Packet:
    def __init__(self, rid, payload):
        self.payload = payload
        self.rid = rid
        self._digest = None
        self._sig = None

    def packets(self):
        r = [self.header_packet()]
        r.extend(self.data_packets())
        return r

    def header_packet(self):
        digest = self.digest()
        sig = self.signature()
        return struct.pack('> H i 12s 40s', self.rid, len(self.payload), digest[:12], sig)

    # fragment payload into data packets, and zero-pad
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
        if (self._digest):
            return self._digest
        sha1 = hashlib.sha1()
        sha1.update(struct.pack('> H', self.rid))
        sha1.update(self.payload)
        self._digest = sha1.digest()
        return self._digest

    def signature(self):
        if self._sig:
            return self._sig
        digesthex = binascii.hexlify(self.digest())
        p = subprocess.Popen(['./lib/signer', 'sign'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(digesthex)
        outlines = out.split("\n")
        result = outlines[1]
        self._sig = binascii.unhexlify(result)
        return self._sig
