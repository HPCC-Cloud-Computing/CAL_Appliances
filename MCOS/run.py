import eventlet

eventlet.monkey_patch()
from eventlet import wsgi
from optparse import OptionParser
import os

from django.core.wsgi import get_wsgi_application

MAX_GREEN_THREADS = 25


def run_wsgi_app(app, port=8080):
    """Run a wsgi compatible app using eventlet"""
    print "starting eventlet server on port %i" % port
    wsgi.server(
        eventlet.listen(('', port)),
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
        help="DJANGO_SETTINGS_MODULE", default="mcs.settings.local"
    )
    parser.add_option(
        "-t", "--threads", type=int,
        help="Maximum green threads to use", default=25
    )

    (options, args) = parser.parse_args()

    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings

    run_wsgi_app(get_wsgi_application(), options.port)
