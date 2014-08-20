import collections
import packet


class DataQueue:
    def __init__(self, ctx):
        self.logger = ctx.get_logger().bind(origin='DataQueue')
        self.ctx = ctx
        self.drainEventHandlers = []
        self.queues = {}

    def id2q(self, cid):
        if cid not in self.queues:
            self.queues[cid] = collections.deque()
            self.logger.info("data_queue_created", cid=cid)
        return self.queues[cid]

    def add_message(self, rid, payload):
        """Send message on all connections (ie, to all gateways+badges)"""

        packets = packet.Packet(rid, payload).packets()
        self.logger.debug("enqueuing_message", cid='*', rid=rid, payload_len=len(payload), num_queues=len(self.queues), num_packets=len(packets))
        # Serialize and add packets to the queue for this payload
        for cid, queue in self.queues.iteritems():
            self.logger.debug("enqueuing_message_on_cid", cid=cid, rid=rid, payload_len=len(payload), numpackets=len(packets))
            queue.extend(packets)
        return True

    def add_transmit_window_to_all_connections(self, rid, payload, duration_in_sec):
        """Add transmit window to all connections that don't already have one"""

        self.logger.debug("add_transmit_window_to_all_connections", cid='*', rid=rid, payload_len=len(payload), num_queues=len(self.queues), duration_in_sec=duration_in_sec)
        packets = packet.Packet(rid, payload).packets()
        for cid, queue in self.queues.iteritems():
            if not self._contains_float_in_queue(cid):
                self.logger.debug("add_transmit_window", cid=cid, duration_in_sec=duration_in_sec)
                queue.extend(packets)
                queue.append(duration_in_sec)


    def _contains_float_in_queue(self, connectionId):
        """a float in the queue means there's already a transmit window scheduled."""
        queue = self.id2q(connectionId)
        for content in queue:
            if isinstance(content, float):
                return True
        return False


    def add_message_on_cid(self, connectionId, rid, payload):
        """Send message to a specific connection (ie, to one gateway only)"""

        self.logger.debug("enqueuing_message", cid=connectionId, rid=rid, payload_len=len(payload))

        queue = self.id2q(connectionId)
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
            # TODO
            self.logger.info("removing_connection", cid=connectionId)
        else:
            self.logger.warn("no_such_q", cid=connectionId)

    def get_next_packet(self, connectionId):
        queue = self.id2q(connectionId)
        if len(queue) > 0:
            return queue.popleft()

        # If we get here the queue has drained
        for callback in self.drainEventHandlers:
            callback(connectionId)
        return None

    def add_drain_handler(self, callback):
        self.drainEventHandlers.append(callback)
