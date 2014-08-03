import logging
import collections
import hashlib
import subprocess
import binascii
import struct

class DataQueue:
    def __init__(self):
        self.logger = logging.getLogger('dataQueue')
        self.drainEventHandlers = []
        self.queues = {}

    def add_message(self, connectionId, rid, payload):    
        self.logger.debug("Queuing data for connection %d and rid %d. Length %d", connectionId, rid, len(payload))

        if connectionId not in self.queues:
            self.queues[connectionId] = collections.deque()
            self.logger.info("Data queue for connection %d has been created", connectionId)
        queue = self.queues[connectionId]

        # Create hash over message
        sha1 = hashlib.sha1()
        sha1.update(struct.pack('> H', rid));
        sha1.update(payload);
        digest = sha1.digest()

        # Sign hash
        # ToDo: Pass in private key
        p = subprocess.Popen(['./uECC/signer', 'sign'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(binascii.hexlify(digest))
        if (binascii.unhexlify(out.split("\n")[0]) != digest):
            sys.exit("Signer process didn't return correct hash.")
        signature = binascii.unhexlify(out.split("\n")[1]);

        # Package message up
        packet = struct.pack('> H i 12s 40s', rid, len(payload), digest[:12], signature);
        queue.append(packet)

        # Split by packet
        currentPosition = 0;
        while currentPosition < len(payload):
            packet = payload[currentPosition:currentPosition+56];
            while len(packet) < 56:
                packet += b"\x00"
            queue.append(struct.pack('> H 56s', rid, packet));
            currentPosition += 56

    def delete_connection(self, connectionId):
        if connectionId in self.queues:
            self.logger.info("Removing connection id from data queue: %d", connectionId)
        else: 
            self.logger.warn("No data queue for connection id %d found", connectionId)

    def get_next_packet(self, connectionId):
        if connectionId in self.queues:
            queue = self.queues[connectionId]
            if len(queue) > 0:
                return queue.popleft()

        # If we get here the queue has drained
        for callback in self.drainEventHandlers:
            callback(connectionId)
        return None
        
    def add_drain_handler(self, callback):
        self.drainEventHandlers.append(callback)
        
        

