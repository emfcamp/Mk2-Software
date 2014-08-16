

class Stats(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = ctx.get_logger().bind(origin='stats')
        ctx.sub('gateway_connected', self.on_gw_connected)
        ctx.sub('gateway_disconnected', self.on_gw_disconnected)

    def on_gw_connected(self, connectionId):
        self.logger.info('gateway_connected', cid=connectionId)

    def on_gw_disconnected(self, connectionId):
        self.logger.info('gateway_disconnected', cid=connectionId)
