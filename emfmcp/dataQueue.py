import logging
import collections
import packet


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
        # Serialize and add packets to the queue for this payload
        p = packet.Packet(rid, payload)
        queue.extend(p.packets())

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
