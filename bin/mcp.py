#!/usr/bin/env python
import json
import emfmcp
from pydispatch import dispatcher


# Global state object, passed around everywhere
# also our pub/sub api.
class Context(object):
    def __init__(self):
        pass

    def pub(self, signal_name, **rest):
        dispatcher.send(signal=signal_name, **(rest or {}))

    def sub(self, signal_name, callback, sender=dispatcher.Any):
        dispatcher.connect(callback, signal=signal_name, sender=sender)

    __slots__ = ('config', 'q', 'tcpserver', 'mcs', 'dcs', 'get_logger', 'badgedb')


ctx = Context()
ctx.get_logger = emfmcp.GetLoggerGetter()

ctx.config = json.load(open('etc/config.json'))
ctx.get_logger().info("loaded_config", config=json.dumps(ctx.config))
ctx.q = emfmcp.DataQueue(ctx)
ctx.tcpserver = emfmcp.TcpServer(ctx)
ctx.mcs = emfmcp.MainChannelSender(ctx)
ctx.dcs = emfmcp.DiscoveryAnnouncer(ctx)
ctx.dcs.start()
ctx.mcs.start()
twa = emfmcp.TransmitWindowAnnouncer(ctx)
twa.start()
emfmcp.HTTPd.listen(ctx, 8888)
ctx.badgedb = emfmcp.BadgeDB(ctx)

stats = emfmcp.Stats(ctx)
main = emfmcp.Main(ctx)
main.start()
