from django.http import HttpResponse
from mcs.wsgi import RINGS


def index(request):
    x = RINGS.x
    for i in range(1, 50000000):
        RINGS.x += 1
    return HttpResponse("Hello, world. You're at the polls index." + str(RINGS.x))
