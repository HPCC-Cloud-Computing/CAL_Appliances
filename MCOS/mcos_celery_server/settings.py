from __future__ import absolute_import, unicode_literals
import os
import sys
import time
import django
from sys import path
from django.utils import timezone
from os.path import abspath, dirname
from kombu import Exchange, Queue

from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME
# print MCOS_CLUSTER_NAME
# ^^^ The above is required if you want to import from the celery
# library.  If you don't have this then `from celery.schedules import`
# becomes `proj.celery.schedules` in Python 2.x since it allows
# for relative imports by default.

# Celery settings

broker_url = 'amqp://mcos:bkcloud@localhost'

#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
accept_content = ['json', ]
result_backend = 'rpc://'
task_serializer = 'json'
include = ['mcos_celery_server.tasks']
task_routes = {
    'mcos_celery_server.tasks.update_cluster_status':
        {'queue': 'update_cluster_status_' + MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange',
         'routing_key': 'update_cluster_status',}
}

task_queues = (
    # Queue('feed_tasks',    routing_key='feed.#'),
    # Queue('regular_tasks', routing_key='task.#'),
    Queue('update_cluster_status_' + MCOS_CLUSTER_NAME,
          exchange=Exchange('mcos_exchange', type='direct'),
          routing_key='update_cluster_status'),
)
