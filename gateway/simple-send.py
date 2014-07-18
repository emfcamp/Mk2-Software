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

# Set up serial stuff
ser = serial.Serial(sys.argv[1], 9600)

# Set up message
payload = "".join(sys.stdin.readlines())
receiver = int(sys.argv[2])

sha1 = hashlib.sha1()
sha1.update(struct.pack('> H', receiver));
sha1.update(payload);
digest = sha1.digest()

signature = "012345678901234567890123456789AB" # Replace with some form of signature

packet = struct.pack('> H i 20s 32s', receiver, len(payload), digest, signature);
ser.write(packet);
ser.flush();
time.sleep(0.1)

currentPosition = 0;
while currentPosition < len(payload):
	packet = payload[currentPosition:currentPosition+56];
	while len(packet) < 56:
		packet += b"\x00"
	ser.write(struct.pack('> H 56s', receiver, packet));
	ser.flush()
	time.sleep(0.01)
	currentPosition += 56

