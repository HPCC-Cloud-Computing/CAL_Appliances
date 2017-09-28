from __future__ import absolute_import, unicode_literals
import os
import sys
import time
import django
from sys import path
from os.path import abspath, dirname

from celery import Celery

# import memcache
#
# client = memcache.Client([('127.0.0.1', 11211)])
# from .settings import CELERY_BROKER_URL

app = Celery('mcos_celery_server')
app.config_from_object('mcos_celery_server.settings')


# Load task modules from all registered Django app configs.
# app.autodiscover_tasks(['django_celery.'])


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
