#!/usr/bin/env python
import json
import emfmcp


# Global state object, passed around everywhere
class Context(object):
    __slots__ = ('config', 'q', 'tcpserver', 'mcs', 'dcs', 'get_logger')


ctx = Context()
ctx.get_logger = emfmcp.GetLoggerGetter()


ctx.config = json.load(open('etc/config.json'))
ctx.get_logger().info("loaded_config", config=json.dumps(ctx.config))
ctx.q = emfmcp.DataQueue(ctx)
ctx.tcpserver = emfmcp.McpTcpServer(ctx)
ctx.mcs = emfmcp.MainChannelSender(ctx)
ctx.dcs = emfmcp.DiscoveryChannelTimer(ctx)

ctx.dcs.start()
ctx.mcs.start()
emfmcp.HTTPd.listen(ctx, 8888)

main = emfmcp.Main(ctx)
main.start()
