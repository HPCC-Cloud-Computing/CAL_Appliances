from __future__ import absolute_import, unicode_literals
import eventlet

eventlet.monkey_patch()
import os
import sys
import time
import django
from django.utils.timezone import tzinfo
from sys import path
from django.utils import timezone
from os.path import abspath, dirname

path.insert(0, os.getcwd())
# from mcos.settings.shared import PERIODIC_SEND_STATUS_TIME
PERIODIC_SEND_STATUS_TIME = 10
from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME
from mcos.settings.base import TIME_ZONE
from mcos_celery_server import tasks


# for path_name in path:
#     print path_name

def setup_django_db_context(db_setting_modules):
    os.environ['DJANGO_SETTINGS_MODULE'] = db_setting_modules
    django.setup()


def check_internal_cluster(current_cluster):
    return True


setup_django_db_context(db_setting_modules='mcos.settings')
from mcos.apps.admin.system.models import SystemCluster
from mcos.apps.admin.system.models import ObjectServiceInfo

not_exit = True
while not_exit:
    try:
        current_cluster = SystemCluster.objects.filter(
            name=MCOS_CLUSTER_NAME).first()
        if check_internal_cluster(current_cluster) is True:
            current_time = timezone.now()
            # print(current_time)
            # print(time.mktime(current_time.timetuple()))
            tasks.update_cluster_status.delay(
                str(current_cluster.id),
                SystemCluster.ACTIVE,
                time.mktime(current_time.timetuple())
            )
            # current_cluster_id = str(current_cluster.id)
            # current_time =  time.mktime(current_time.timetuple())
            # dt = datetime.fromtimestamp(1346236702)
            # print time.mktime(dt.timetuple())
            pass
        else:
            pass
        time.sleep(PERIODIC_SEND_STATUS_TIME)

    except Exception as e:
        print(e)
        # sys.exit(1)
