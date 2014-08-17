import json
import tornado.ioloop
import tornado.web
import binascii
from tornado.web import url, RequestHandler
#import tornado.websocket


class Application(tornado.web.Application):
    def __init__(self, ctx, handlers):
        self.ctx = ctx
        self.logger = ctx.get_logger().bind(origin='web')
        settings = dict(debug=True)
        super(Application, self).__init__(handlers, **settings)
        self.config = ctx.config
        self.q = ctx.q


class IndexHandler(RequestHandler):
    def get(self):
        self.write("OK\n")


class StatusHandler(RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'application/json')
        ctx = self.application.ctx
        gateways = {}
        for (cid, connection) in ctx.tcpserver.connections.items():
            gw = connection.toJSON()
            gw['badges'] = ctx.badgedb.get_badges_by_cid(cid)
            gateways[cid] = gw

        j = {"num_gateways": len(ctx.tcpserver.connections),
             "gateways": gateways
             }
        self.write(json.dumps(j))


class SendHandler(RequestHandler):
    def post(self):
        rid = int(self.get_argument('rid', '-1'))
        msg = self.request.body
        self.application.logger.info("send_msg", rid=rid, msg=binascii.hexlify(msg))
        self.application.q.add_message(rid, msg)
        self.write("OK")


#class WebSocket(tornado.websocket.WebSocketHandler):
#    def open(self):
#        self.application.logger.info('websocket_opened')
#
#    def on_message(self, message):
#        self.write_message(u"You said: " + message)
#
#    def on_close(self):
#        self.application.logger.info('websocket_closed')


def listen(ctx, port=8888):
    static_path = "./htdocs"
    application = Application(ctx, [
        url(r"/status.json", StatusHandler),
        url(r"/send", SendHandler),
        #url(r"/ws", WebSocket),
        url(r"/(.*)", tornado.web.StaticFileHandler, {'path': static_path}),
    ])
    application.listen(port)
