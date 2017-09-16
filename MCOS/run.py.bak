"""
WSGI config for mcos project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""
import eventlet

eventlet.monkey_patch()


from eventlet import wsgi
from optparse import OptionParser
from os.path import abspath, dirname
from sys import path
from mcos.system_setting import SystemConnectionError, connect_to_system
import os

from django.core.wsgi import get_wsgi_application

# from all_ring import RingDict

SITE_ROOT = dirname(dirname(abspath(__file__)))
# path.append(SITE_ROOT)
path.insert(0, SITE_ROOT)

MAX_GREEN_THREADS = 25
# RINGS = RingDict()


def run_wsgi_app(app, port=8000):
    """Run a wsgi compatible app using eventlet"""
    print "starting eventlet server on port %i" % 8000
    wsgi.server(
        eventlet.listen(('', 8000)),
        app,
        max_size=MAX_GREEN_THREADS,
    )


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "-p", "--port", type=int, help="Port to run on", default=8080
    )
    parser.add_option(
        "-s", "--settings", type=str,
        help="DJANGO_SETTINGS_MODULE", default="mcos.settings"
    )
    parser.add_option(
        "-t", "--threads", type=int,
        help="Maximum green threads to use", default=25
    )

    (options, args) = parser.parse_args()

    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
    try:
        connect_to_system(options.settings)
        application = get_wsgi_application()
        run_wsgi_app(application, options.port)
    except SystemConnectionError as e:
        print("Cannot connect to system. Server will be exited.")
