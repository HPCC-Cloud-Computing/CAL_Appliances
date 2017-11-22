from __future__ import absolute_import, unicode_literals
# Create your tasks here
# import memcache
import os
import django
import time
import os
import sys
import pytz
import json
from sys import path
import uuid
from django.utils import timezone
from os.path import abspath, dirname

path.insert(0, os.getcwd())
from mcos.settings.mcos_conf import PERIODIC_CHECK_STATUS_TIME
from .celery import app

# django db setup
os.environ['DJANGO_SETTINGS_MODULE'] = 'mcos.settings'
django.setup()
from mcos.apps.admin.system.models import SystemCluster
from mcos.apps.admin.shared_database.models import Cluster, Ring, \
    UpdatedRingCluster
from mcos.apps.admin.shared_database.connection import SharedDatabaseConnection
from mcos.apps.utils.cache import MemcacheClient
from .ring_db import Session as LocalRingDbSession, Ring as LocalRing


@app.task()
# add ring info to shared db, to memcached and write ring to disk
# in current version, only support add new ring, current update ring
# (create new version ring) is unsupported
def add_ring_info(ring_dict_str, cluster_id):
    try:
        print(cluster_id)
        memcache_client = MemcacheClient()
        added_ring = json.loads(ring_dict_str)
        # add ring data to shared database and set current cluster
        # in updated cluster
        # get ring_info from shared database
        shared_db_conn = SharedDatabaseConnection()
        ring_info = shared_db_conn.session.query(Ring).filter_by(
            id=str(added_ring['id'])).first()
        if ring_info is None:
            create_new = True
            print("ring " + added_ring['name'] + " is not exist. "
                                                 "Create new entry for this ring.")
            ring_info = Ring(id=added_ring['id'], name=added_ring['name'],
                             version=added_ring['version'])
        else:
            create_new = False
            print(ring_info.id)
            print(ring_info.name)

        current_cluster = shared_db_conn.session.query(Cluster).filter_by(
            id=str(cluster_id)).first()
        if create_new is True:
            ring_info.updated_clusters.append(current_cluster)
            shared_db_conn.session.add(ring_info)
            shared_db_conn.session.commit()
        shared_db_conn.close()
        # write account_ring to disk
        with open('rings/' + str(added_ring['name']) + '_' + str(
                added_ring['version']) + '.txt', 'wt') \
                as ring_file:
            ring_file.write(ring_dict_str)
        # write account_ring to local ring db
        local_ring_conn = LocalRingDbSession()
        local_ring = local_ring_conn.query(Ring). \
            filter_by(name=str(added_ring['name'])).first()
        if local_ring is None:
            local_ring = LocalRing(
                id=added_ring['id'],
                name=added_ring['name'],
                ring_type=added_ring['ring_type'],
                version=int(added_ring['version'])
            )
            local_ring_conn.add(local_ring)
            local_ring_conn.commit()
            local_ring_conn.close()
        else:
            pass
            # implement for ring update - next version
        # push ring to memcached
        current_rings = memcache_client.get_data('rings')
        if check_ring_exist(added_ring['name']) is False:
            ring_info = {
                'name': added_ring['name'],
                'version': ['1', ],
                'ring_type': added_ring['ring_type'],

            }
            current_rings.append(ring_info)
            memcache_client.set('rings', current_rings)
            memcache_client.set('ring_' + added_ring['name'] + '_' +
                                str(added_ring['version']), ring_dict_str)

        else:
            # implement for ring update - next version
            pass
        return True
    except Exception as e:
        print(e)
        return False


@app.task()
def get_ring_info(ring_id):
    try:
        local_ring_conn = LocalRingDbSession()
        local_ring = local_ring_conn.query(Ring). \
            filter_by(id=str(ring_id)).first()
        with open('rings/' + str(local_ring.name) + '_' + str(
                local_ring.version) + '.txt', 'r') \
                as ring_file:
            ring_data = ring_file.read()
        return ring_data
    except Exception as e:
        print(e)
        return "error"


# check if a ring have name ring_name is exist in Memcache server or not
# function used to check a ring exist in ring list in memcache or not
# ring list format in memcached:
# rings : [ring_dict_1,ring_dict_2,...ring_dict_n]
# ring_dict_i : {'name':ring_i_name,'versions':[v1,v2,....vi]}
# each version ring of a ring has a pair key_value in memcache that:
# "ring_"+ring_name+"_"+ring_version: version_ring_data

@app.task()
def check_ring_exist(ring_name):
    is_exist = False
    memcache_client = MemcacheClient()
    rings = memcache_client.get('rings')
    for check_ring in rings:
        if ring_name == check_ring['name']:
            is_exist = True
            break
    return is_exist


# get container list
@app.task
def get_container_list(user_name):
    container_list = []
    for i in range(1, 20):
        container_list.append(str(i))
    return container_list


import random
import time


def strTimeProp(start, end, format, prop):
    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def randomDate(start, end, prop):
    return strTimeProp(start, end, '%m/%d/%Y %I:%M %p', prop)


@app.task
def get_container_info(user_name, container_name):
    import random
    data_object_list = []
    total_object = random.randint(5, 20)
    container_size = 0
    for i in range(0, total_object):
        data_object_info = {
            'file_name': str(random.randint(5, 100)),
            'last_update': str(randomDate("1/1/2015 1:30 PM",
                                          "1/1/2017 4:50 AM",
                                          random.random())),
            'size': str(random.randint(5, 30000))
        }
        container_size += int(data_object_info['size'])
        data_object_list.append(data_object_info)
    container_info = {
        'name': container_name,
        'date_created': ' Nov 15, 2017',
        'object_count': len(data_object_list),
        'object_list': data_object_list,
        'size': container_size
    }
    return container_info
