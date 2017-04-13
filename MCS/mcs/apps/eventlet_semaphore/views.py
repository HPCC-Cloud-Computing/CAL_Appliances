from django.http import HttpResponse
from mcs.wsgi import RINGS
from eventlet.green import urllib2
from mcs.wsgi import global_rings

url = "http://www.google.com/intl/en_ALL/images/logo.gif"


# process in this method can read and change shared data
def write_ring_1(request):
    result = []

    written_ring = global_rings[1]
    with written_ring:
        for i in range(1, 501):
            written_ring.ring += 1
            if i % 5 == 0:
                urllib2.urlopen(url).read()
                result.append(written_ring.ring)
                urllib2.urlopen(url).read()
                # buffer_file = open('ring.txt', 'a', 0)
                # buffer_file.write('hello' + str(RINGS.x) + '\n')
                # buffer_file.close()
        return_arr = ""
        for i in result:
            return_arr += str(i) + '   '
        written_ring.version += 1

    return HttpResponse(return_arr)


# process in this method mustn't change shared data, it only can read data
# one note for you is, each time we want to read ring data, we must check ring version first
# because when your request switch to I/O, when we wait I/O return, this ring may be changed.
def read_ring_1(request):
    reading_ring = global_rings[1]
    if not reading_ring.locked():
        # get version of current ring
        ring_version = reading_ring.version
        return HttpResponse(reading_ring.ring)
    else:
        return HttpResponse('server busy')

