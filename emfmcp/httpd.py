import tornado.ioloop
import tornado.web
import logging
from tornado.web import url, RequestHandler


class Application(tornado.web.Application):
    def __init__(self, config, q, handlers):
        self.logger = logging.getLogger('HTTPd')
        settings = dict(debug=True)
        super(Application, self).__init__(handlers, **settings)
        self.config = config
        self.q = q


class IndexHandler(RequestHandler):
    def get(self):
        self.write("OK\n")


class SendHandler(RequestHandler):
    def post(self):
        rid = int(self.get_argument('rid', '-1'))
        cid = int(self.get_argument('connection', '-1'))
        msg = self.request.body
        self.application.logger.debug("rid: %d, cid: %d, msg: %s" % (rid, cid, msg))

        self.application.q.add_message(cid, rid, msg)
        self.write("OK")


def listen(config, dataQueue, port=8888):
    application = Application(config, dataQueue, [
        url(r"/", IndexHandler),
        url(r"/send", SendHandler),
    ])
    application.listen(port)
