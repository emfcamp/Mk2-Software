import collections
import packet


class DataQueue:
    def __init__(self, ctx):
        self.logger = ctx.get_logger().bind(origin='DataQueue')
        self.ctx = ctx
        self.drainEventHandlers = []
        self.queues = {}

    def add_message(self, rid, payload):
        """Send message on all connections (ie, to all gateways+badges)"""

        self.logger.debug("enqueuing_message", cid='*', rid=rid, payload_len=len(payload))
        # Serialize and add packets to the queue for this payload
        packets = packet.Packet(rid, payload).packets()
        for (cid, queue) in self.queues:
            queue.extend(packets)
        return True

    def add_message_on_cid(self, connectionId, rid, payload):
        """Send message to a specific connection (ie, to one gateway only)"""

        self.logger.debug("enqueuing_message", cid=connectionId, rid=rid, payload_len=len(payload))

        if connectionId not in self.queues:
            self.queues[connectionId] = collections.deque()
            self.logger.info("data_queue_created", cid=connectionId)
        queue = self.queues[connectionId]
        # Serialize and add packets to the queue for this payload
        p = packet.Packet(rid, payload)
        queue.extend(p.packets())
        return True

    def add_message_on_badge(self, b, rid, payload):
        """Send a message to a badge/bid, by looking up the registered gateway"""
        # b should be the Badge() object, or the badge.id
        if isinstance(b, int):
            badge = self.ctx.badgedb.get_badge_by_id(b)
        else:
            badge = b

        if badge is None:
            self.logger.warn('badge_not_found_for_sending', badge=b, rid=rid)
            return False
        return self.add_message_on_cid(badge.gwid, rid, payload)

    def delete_connection(self, connectionId):
        if connectionId in self.queues:
            self.logger.info("removing_connection", cid=connectionId)
        else:
            self.logger.warn("no_such_q", cid=connectionId)

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
