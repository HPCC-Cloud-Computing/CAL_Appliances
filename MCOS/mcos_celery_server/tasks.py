from __future__ import absolute_import, unicode_literals
# Create your tasks here
# import memcache
import os
import django
import time
import os
import sys
import pytz
from sys import path
from django.utils import timezone
from os.path import abspath, dirname

path.insert(0, os.getcwd())
from mcos.settings.mcos_conf import PERIODIC_CHECK_STATUS_TIME
from .celery import app

os.environ['DJANGO_SETTINGS_MODULE'] = 'mcos.settings'
django.setup()
from mcos.apps.admin.system.models import SystemCluster


@app.task(ignore_result=True)
def update_cluster_status(cluster_id, cluster_status, update_timestamp):
    try:
        print "input info"
        print cluster_id
        print cluster_status
        print update_timestamp
        print "end input info"
        msg_sender_cluster = SystemCluster.objects.filter(
            id=cluster_id).first()
        current_time = timezone.now()
        update_time = pytz.utc.localize(
            timezone.datetime.fromtimestamp(update_timestamp))
        cluster_expiry_time = current_time - timezone.timedelta(
            seconds=PERIODIC_CHECK_STATUS_TIME)
        print cluster_expiry_time
        print update_time
        print current_time
        print msg_sender_cluster.last_update
        # only check message in valid time interval
        if update_time >= cluster_expiry_time and \
                update_time >= msg_sender_cluster.last_update:
            msg_sender_cluster.status = cluster_status
            msg_sender_cluster.last_update= update_time
            msg_sender_cluster.save()
    except Exception as e:
        print e


# @app.task(ignore_result=True)
# def add_cluster(cluster_name, address_ip, address_port):
#     print(
#         "received: " + str(cluster_name) + ' - ' +
#         str(address_ip) + ' - ' + str(address_port))
#     try:
#
#         new_system_cluster = SystemCluster(name=cluster_name,
#                                            address_ip=address_ip,
#                                            address_port=address_port)
#         client = memcache.Client([('127.0.0.1', 11211)])
#         client.incr('celery_server_counter')
#         print client.get("celery_server_counter")
#         time.sleep(client.get("celery_server_counter"))
#         new_system_cluster.save()
#     except Exception as e:
#         print e


@app.task
def mul(x, y):
    return x * y
