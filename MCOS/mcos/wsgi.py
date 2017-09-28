"""
WSGI config for mcos project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""
import eventlet

eventlet.monkey_patch()
import os
from eventlet import wsgi
from django.core.wsgi import get_wsgi_application
import time
from optparse import OptionParser
from os.path import abspath, dirname
from sys import path
from system_setup import SystemConnectionError, connect_to_system
from mcos.settings.mcos_conf import MCOS_PORT


SITE_ROOT = dirname(dirname(abspath(__file__)))
path.insert(0, SITE_ROOT)
path.insert(0, os.getcwd())

#
MAX_GREEN_THREADS = 25
# from all_ring import RingDict
# RINGS = RingDict()

path.insert(0, os.getcwd())
print os.getcwd()

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
# from all_ring import RingDict

SITE_ROOT = dirname(dirname(abspath(__file__)))
# path.append(SITE_ROOT)
path.insert(0, SITE_ROOT)
# RINGS = RingDict()

SYSTEM_INFO = {
    # id of cluster which is holding connect_to_system lock
    'cts_lock_cluster_id': 'none',
    # id of current cluster is running
    'current_cluster_id': 'none',
    # check if user dash board is enabled or not
    'enable_user_dashboard': False

}


def setup_system_and_start_servers():

    try:
        connect_to_system('mcos.settings', SYSTEM_INFO)
        application = get_wsgi_application()
        run_wsgi_app(eventlet, wsgi, application, int(MCOS_PORT))
    except Exception as e:
        print("Cannot connect to system. Server will be exited. ")
        print("Reason: " + e.message)


def run_wsgi_app(eventlet, wsgi, app, port):
    """Run a wsgi compatible app using eventlet"""
    print "starting eventlet server on port %i" % port
    wsgi.server(
        eventlet.listen(('', port)),
        app,
        max_size=MAX_GREEN_THREADS,
    )

if __name__ == "__main__":
    setup_system_and_start_servers()
