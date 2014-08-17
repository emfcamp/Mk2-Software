import tornado.ioloop
import tornado.web
import binascii
from tornado.web import url, RequestHandler



class Application(tornado.web.Application):
    def __init__(self, ctx, handlers):
        self.logger = ctx.get_logger().bind(origin='web')
        settings = dict(debug=True)
        super(Application, self).__init__(handlers, **settings)
        self.config = ctx.config
        self.q = ctx.q


class IndexHandler(RequestHandler):
    def get(self):
        self.write("OK\n")


class SendHandler(RequestHandler):
    def post(self):
        rid = int(self.get_argument('rid', '-1'))
        #cid = int(self.get_argument('connection', '-1'))
        msg = self.request.body
        self.application.logger.info("send_msg", rid=rid, msg=binascii.hexlify(msg))

        self.application.q.add_message(rid, msg)
        self.write("OK")


def listen(ctx, port=8888):
    application = Application(ctx, [
        url(r"/", IndexHandler),
        url(r"/send", SendHandler),
    ])
    application.listen(port)
