# coding: utf-8
from test.util import build_grab, exclude_grab_transport
from test.util import BaseGrabTestCase
import tornado.gen
from tornado.ioloop import IOLoop

from grab.error import (GrabInternalError, GrabTimeoutError)


class GrabTimeoutCase(BaseGrabTestCase):
    def setUp(self):
        self.server.reset()

    def test_timeout(self):

        def callback(server):
            server.set_status(200)
            server.write('x')
            server.write('y')
            for x in range(4):
                yield {'type': 'sleep', 'time': 0.5}
                server.write('y')
                server.flush()
            server.finish()

        self.server.response['callback'] = callback
        g = build_grab()
        g.setup(timeout=1, url=self.server.get_url())
        self.assertRaises(GrabTimeoutError, g.request)
