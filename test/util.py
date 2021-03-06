import os
import shutil
import tempfile
import functools
from test_server import TestServer
from unittest import TestCase
import logging
from six.moves.urllib.request import urlopen
import socket
import time
from contextlib import contextmanager
from tempfile import mkdtemp, mkstemp
from shutil import rmtree

from grab import Grab

logger = logging.getLogger('test.util')
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_SERVER_PORT = 9876
ADDRESS = 'localhost'
EXTRA_PORT1 = TEST_SERVER_PORT + 1
EXTRA_PORT2 = TEST_SERVER_PORT + 2

GLOBAL = {
    'backends': [],
    'mp_mode': False,
    'grab_transport': None,
    'spider_transport': None,
}


@contextmanager
def temp_dir(root_dir=None):
    dir_ = mkdtemp(dir=root_dir)
    yield dir_
    rmtree(dir_)


@contextmanager
def temp_file(root_dir=None):
    fd, file_ = mkstemp(dir=root_dir)
    yield file_
    os.close(fd)
    os.unlink(file_)


def build_grab(*args, **kwargs):
    """Builds the Grab instance with default options."""
    kwargs.setdefault('transport', GLOBAL['grab_transport'])
    return Grab(*args, **kwargs)


def build_spider(cls, **kwargs):
    """Builds the Spider instance with default options. Also handles
    `--mp-mode` option that is configured globally."""
    kwargs.setdefault('mp_mode', GLOBAL['mp_mode'])
    kwargs.setdefault('grab_transport', GLOBAL['grab_transport'])
    kwargs.setdefault('transport', GLOBAL['spider_transport'])
    if kwargs['mp_mode']:
        kwargs.setdefault('parser_pool_size', 2)
    else:
        kwargs['parser_pool_size'] = 1
    return cls(**kwargs)


class BaseGrabTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server()#GLOBAL['test_server']

    def setUp(self):
        self.server.reset()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()


def multiprocess_mode(mode):
    def wrapper_builder(func):
        def wrapper(self, *args, **kwargs):
            if mode != GLOBAL['mp_mode']:
                logger.debug('Skipping %s:%s:%s. Reason: need '
                             '--mp-mode=%s' % (
                                 func.__module__,
                                 self.__class__.__name__,
                                 func.__name__, mode))
            else:
                return func(self, *args, **kwargs)
        return wrapper
    return wrapper_builder


def start_server():
    logger.debug('Starting test server on %s:%s' % (ADDRESS, TEST_SERVER_PORT))
    server = TestServer(address=ADDRESS, port=TEST_SERVER_PORT,
                        extra_ports=[EXTRA_PORT1, EXTRA_PORT2])
    server.start()
    '''
    # Ensure that test server works
    old_timeout = socket.getdefaulttimeout()
    ok = False
    for x in range(6):
        socket.setdefaulttimeout(0.5)
        try:
            urlopen('http://localhost:%d/' % TEST_SERVER_PORT).read()
        except Exception as ex:
            logger.error('', exc_info=ex)
            time.sleep(0.1)
        else:
            ok = True
            break
    socket.setdefaulttimeout(old_timeout)
    if not ok:
        raise Exception('Test server does not respond.')
    else:
    '''
    #GLOBAL['test_server'] = server
    return server


def stop_server():
    logger.debug('Stopping test server')
    #GLOBAL['test_server'].stop()


def exclude_grab_transport(*names):
    def decorator(func):
        def caller(*args, **kwargs):
            if GLOBAL['grab_transport'] in names:
                func_name = '%s:%s' % (func.__module__, func.__name__)
                logger.debug('Running test %s for grab transport %s is restricted'
                             % (func_name, GLOBAL['grab_transport']))
                return None
            else:
                return func(*args, **kwargs)
        return caller
    return decorator


def only_grab_transport(*names):
    def decorator(func):
        def caller(*args, **kwargs):
            if GLOBAL['grab_transport'] in names:
                return func(*args, **kwargs)
            else:
                func_name = '%s:%s' % (func.__module__, func.__name__)
                logger.debug('Running test %s for grab transport %s is restricted'
                             % (func_name, GLOBAL['grab_transport']))
                return None
        return caller
    return decorator
