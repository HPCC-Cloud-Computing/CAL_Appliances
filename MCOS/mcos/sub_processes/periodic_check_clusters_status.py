from __future__ import absolute_import, unicode_literals
# import eventlet
# eventlet.monkey_patch()
import sys
import time
import django
from django.utils import timezone
import os
from sys import path
from os.path import abspath, dirname

path.insert(0, os.getcwd())
# print os.getcwd()
# print path
import mcos
from mcos.settings import mcos_conf

# from mcos.settings.shared import PERIODIC_CHECK_STATUS_TIME
PERIODIC_CHECK_STATUS_TIME = 60


def setup_django_db_context(db_setting_modules):
    os.environ['DJANGO_SETTINGS_MODULE'] = db_setting_modules
    django.setup()


setup_django_db_context(db_setting_modules='mcos.settings')
from mcos.apps.admin.system.models import SystemCluster
from mcos.apps.admin.system.models import ObjectServiceInfo

not_exit = True
while not_exit:
    try:
        current_time = timezone.now()
        # print current_time
        # print current_time
        clusters = SystemCluster.objects.all()
        for cluster in clusters:
            cluster_expiry_time = cluster.last_update + timezone.timedelta(
                seconds=PERIODIC_CHECK_STATUS_TIME)
            if current_time > cluster_expiry_time:
                # print("cluster" + str(cluster.id) + " is expired!")
                if cluster.status != SystemCluster.SHUTOFF:
                    cluster.status = SystemCluster.SHUTOFF
                    cluster.save()
        time.sleep(PERIODIC_CHECK_STATUS_TIME)
    except Exception as e:
        print e
        # sys.exit(1)
