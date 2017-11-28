from __future__ import absolute_import, unicode_literals
import os
import sys
import time
import django
from sys import path
from django.utils import timezone
from os.path import abspath, dirname
from kombu import Exchange, Queue

from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME, MESSAGE_QUEUE_IP

# print MCOS_CLUSTER_NAME
# ^^^ The above is required if you want to import from the celery
# library.  If you don't have this then `from celery.schedules import`
# becomes `proj.celery.schedules` in Python 2.x since it allows
# for relative imports by default.

# Celery settings

broker_url = 'amqp://mcos:bkcloud@' + MESSAGE_QUEUE_IP

#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
accept_content = ['json', ]
result_backend = 'rpc://'
task_serializer = 'json'
include = ['mcos_resolver_and_ring_server.tasks']

task_routes = {
    'mcos_resolver_and_ring_server.tasks.add_ring_info':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.add_ring_info', },
    'mcos_resolver_and_ring_server.tasks.check_ring_exist':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.check_ring_exist', },
    'mcos_resolver_and_ring_server.tasks.get_ring_info':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.get_ring_info', },

    'mcos_resolver_and_ring_server.tasks.get_account_clusters_ref':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.get_account_clusters_ref', },
    'mcos_resolver_and_ring_server.tasks.get_container_clusters_ref':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.get_container_clusters_ref', },
    # 'mcos_resolver_and_ring_server.tasks.get_container_info':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.get_container_info', },
    #
    # 'mcos_resolver_and_ring_server.tasks.api_get_container_list':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.api_get_container_list', },
    #
    'mcos_resolver_and_ring_server.tasks.get_container_list':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.get_container_list', },
    'mcos_resolver_and_ring_server.tasks.get_container_details':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.get_container_details', },
    'mcos_resolver_and_ring_server.tasks.get_object_list':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.get_object_list', },
    'mcos_resolver_and_ring_server.tasks.create_new_container':
        {'queue': MCOS_CLUSTER_NAME,
         'exchange': 'mcos_exchange_topic',
         'routing_key': MCOS_CLUSTER_NAME + '.create_new_container', },

    #
    # 'mcos_resolver_and_ring_server.tasks.api_create_container':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.api_create_container', },
    # 'mcos_resolver_and_ring_server.tasks.create_container':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.create_container', },
    # 'mcos_resolver_and_ring_server.tasks.populate_new_container':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.populate_new_container', },
    #

    #
    # 'mcos_resolver_and_ring_server.tasks.get_object_list':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.get_object_list', },
    #
    # 'mcos_resolver_and_ring_server.tasks.api_get_object_list':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.api_get_object_list', },
    # 'mcos_resolver_and_ring_server.tasks.create_container':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.create_container', },
    # 'mcos_resolver_and_ring_server.tasks.populate_new_container':
    #     {'queue': MCOS_CLUSTER_NAME,
    #      'exchange': 'mcos_exchange_topic',
    #      'routing_key': MCOS_CLUSTER_NAME + '.populate_new_container', },
}

task_queues = (
    # Queue('feed_tasks',    routing_key='feed.#'),
    # Queue('regular_tasks', routing_key='task.#'),
    Queue(MCOS_CLUSTER_NAME,
          exchange=Exchange('mcos_exchange_topic', type='topic'),
          routing_key=MCOS_CLUSTER_NAME + ".#"),
)
