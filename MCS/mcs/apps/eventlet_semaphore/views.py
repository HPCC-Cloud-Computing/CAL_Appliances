from django.http import HttpResponse
from mcs.wsgi import RINGS
from eventlet.green import urllib2

url = "http://www.google.com/intl/en_ALL/images/logo.gif"


def index(request):
    result = []
    for i in range(1, 500000):
        RINGS.x += 1
        if i % 5000 == 0:
            urllib2.urlopen(url).read()
            result.append(RINGS.x)
            urllib2.urlopen(url).read()
            # buffer_file = open('ring.txt', 'a', 0)
            # buffer_file.write('hello' + str(RINGS.x) + '\n')
            # buffer_file.close()
    return_arr = ""
    for i in result:
        return_arr += str(i) + '   '

    return HttpResponse("Hello, world. You're at the polls index.\n"+return_arr)
