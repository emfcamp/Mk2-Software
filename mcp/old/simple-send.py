# 
# Simple script that sends a message from stdin to badges.
#
# Make sure to configure the stick correctly before you use this:
# +++ <Wait 1 sec>
# ATPK3A
# ATAC
# ATDN
#
# Usage: echo "Test" | python simple-send.py /dev/ttyACM1 40960
# 
# Parameter 1: USB port used for radio
# Parameter 2: Receiver ID in base 10
#

import sys
import hashlib
import M2Crypto
import struct
import time
import serial 
import subprocess
import binascii

# Set up serial stuff
ser = serial.Serial(sys.argv[1], 9600)

# Set up message
payload = "".join(sys.stdin.readlines())
receiver = int(sys.argv[2])

sha1 = hashlib.sha1()
sha1.update(struct.pack('> H', receiver));
sha1.update(payload);
digest = sha1.digest()

# Sign hash
p = subprocess.Popen(['./uECC/signer', 'sign'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate(binascii.hexlify(digest))
if (binascii.unhexlify(out.split("\n")[0]) != digest):
	sys.exit("Signer process didn't return correct hash.")
signature = binascii.unhexlify(out.split("\n")[1]);


packet = struct.pack('> H i 12s 40s', receiver, len(payload), digest[:12], signature);
print packet;
ser.write(packet);
ser.flush();
time.sleep(0.1)

currentPosition = 0;
while currentPosition < len(payload):
	packet = payload[currentPosition:currentPosition+56];
	while len(packet) < 56:
		packet += b"\x00"
	print packet;
	ser.write(struct.pack('> H 56s', receiver, packet));
	ser.flush()
	time.sleep(0.01)
	currentPosition += 56

