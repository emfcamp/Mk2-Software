#!/usr/bin/env python
import time
import json
import emfmcp
import psycopg2
from pydispatch import dispatcher


class Context(object):
    """Global state and config object, passed around everywhere,
       also offers a pub/sub API."""

    def __init__(self, configfile):
        self.config = json.load(open(configfile))
        self.get_logger = emfmcp.GetLoggerGetter()
        self.get_logger().info("loaded_config", config=json.dumps(self.config))
        dbstr = "host='localhost' dbname='schedule' user='tilda' password='tilda'"
        self.conn = psycopg2.connect(dbstr)
        self.conn.set_session(autocommit=True)

    def cursor(self):
        return self.conn.cursor()

    def note(self, msg):
        now = time.strftime("%A, %H:%M:%S")
        self.pub('notable_event', text=msg, time=now)

    def pub(self, signal_name, **rest):
        dispatcher.send(signal=signal_name, **(rest or {}))

    def sub(self, signal_name, callback, sender=dispatcher.Any):
        dispatcher.connect(callback, signal=signal_name, sender=sender)

    __slots__ = ('config',
                 'q',
                 'tcpserver',
                 'mcs',
                 'dcs',
                 'get_logger',
                 'badgedb',
                 'conn',
                 )


ctx = Context('etc/config.json')
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
