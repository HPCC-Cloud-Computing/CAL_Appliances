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
import hashlib
from sys import path
import uuid
import celery
import datetime
from django.utils import timezone
from os.path import abspath, dirname
from celery.result import allow_join_result

path.insert(0, os.getcwd())
from mcos.settings.mcos_conf import PERIODIC_CHECK_STATUS_TIME
from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME as current_cluster_name
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
from .account_db import Session as AccountSession, ContainerInfo
from .container_db import Session as ContainerSession, ObjectInfo


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
@app.task(time_limit=10)
def api_get_container_list(user_name):
    memcache_client = MemcacheClient()
    account_ring = memcache_client.get('ring_account_1')
    if account_ring is None:
        return {
            'result': 'Failed',
            'message': 'account ring is not found'
        }
    account_ring = json.loads(account_ring)
    user_hash = hashlib.md5(user_name)
    partition_pos = int(bin(int(user_hash.hexdigest(), 16))[2:][-account_ring['power_number']:], 2)
    ref_clusters = account_ring['parts'][partition_pos]['cluster_refs']
    with allow_join_result():
        container_list = None
        for cluster_id in ref_clusters:
            cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
            cluster_status = cluster_info.status
            # print(clu)
            if cluster_status == SystemCluster.ACTIVE:
                cluster_name = cluster_info.name
                try:
                    get_container_list_task = get_container_list.apply_async(
                        (user_name,),
                        routing_key=cluster_name + '.get_container_list'
                    )
                    container_list = get_container_list_task.get(timeout=3)
                    if container_list is not None:
                        break
                        # print(container_list)
                except Exception as e:
                    print ('Failed to retrieval container list from cluster ' + cluster_name)
        return container_list
        # return None


@app.task(time_limit=5)
def get_container_list(user_name):
    container_list = []
    account_db_conn = AccountSession()
    container_list_info = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=user_name).all()
    for container in container_list_info:
        container_list.append(container.container_name)
    account_db_conn.close()
    return container_list


@app.task(time_limit=10)
def api_create_container(user_name, container_name):
    memcache_client = MemcacheClient()
    account_ring = memcache_client.get('ring_account_1')
    if account_ring is None:
        return {
            'is_created': False,
            'message': 'account ring is not found'
        }
    account_ring = json.loads(account_ring)
    user_hash = hashlib.md5(user_name)
    partition_pos = int(bin(int(user_hash.hexdigest(), 16))[2:][-account_ring['power_number']:], 2)
    ref_clusters = account_ring['parts'][partition_pos]['cluster_refs']
    is_created = False
    with allow_join_result():
        for cluster_id in ref_clusters:
            cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
            cluster_status = cluster_info.status
            if cluster_status == SystemCluster.ACTIVE:
                cluster_name = cluster_info.name
                try:
                    create_container_task = create_container.apply_async(
                        (user_name, container_name),
                        routing_key=cluster_name + '.create_container'
                    )
                    is_created = create_container_task.get(timeout=3)
                    if is_created:
                        break
                except Exception as e:
                    print ('Failed to create container in cluster ' + cluster_name)
        if is_created:
            return {
                'is_created': True,
                'message': 'new container is created'
            }
        else:
            return {
                'is_created': False,
                'message': 'Container already exists or failed to connect to Container Clusters'
            }
            # return None


@app.task(time_limit=5)
def create_container(user_name, container_name):
    # check if container is already exists
    account_db_conn = AccountSession()
    container_list_info = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=user_name, container_name=container_name).all()
    if len(container_list_info) > 0:
        return True
    try:
        # add new container to database
        new_container = ContainerInfo(
            account_name=user_name,
            container_name=container_name,
            object_count=0,
            size=0,
            date_created=datetime.datetime.utcnow()
        )
        # print(datetime.datetime.utcnow())
        account_db_conn.add(new_container)
        account_db_conn.commit()
        # populate_new_container
        memcache_client = MemcacheClient()
        account_ring = memcache_client.get('ring_account_1')
        account_ring = json.loads(account_ring)
        user_hash = hashlib.md5(user_name)
        partition_pos = int(bin(int(user_hash.hexdigest(), 16))[2:][-account_ring['power_number']:], 2)
        ref_clusters = account_ring['parts'][partition_pos]['cluster_refs']
        with allow_join_result():
            for cluster_id in ref_clusters:
                cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
                print (current_cluster_name)
                if cluster_info.name != current_cluster_name:
                    populate_new_container.apply_async(
                        ({
                             'account_name': new_container.account_name,
                             'container_name': new_container.container_name,
                             'object_count': new_container.object_count,
                             'size': new_container.size,
                             'date_created': str(new_container.date_created)
                         },),
                        routing_key=cluster_info.name + '.populate_new_container'
                    )
        account_db_conn.close()
        return True
    except Exception as e:
        print(e)
        account_db_conn.close()
        return False


@app.task(ignore_result=True)
def populate_new_container(new_container_info):
    # check if container is already exists
    account_db_conn = AccountSession()
    container_list_info = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=new_container_info['account_name'],
                  container_name=new_container_info['container_name']).all()
    if len(container_list_info) > 0:
        return True
    try:
        # add new container to database
        new_container = ContainerInfo(
            account_name=new_container_info['account_name'],
            container_name=new_container_info['container_name'],
            object_count=new_container_info['object_count'],
            size=new_container_info['size'],
            date_created=datetime.datetime.strptime(
                new_container_info['date_created'],
                '%Y-%m-%d %H:%M:%S.%f')
        )
        account_db_conn.add(new_container)
        account_db_conn.commit()
        account_db_conn.close()
    except Exception as e:
        print (e)
        account_db_conn.close()


#
# @app.task(time_limit=5)
# def rpc_get_container_list(user_name):
#     container_info_list = []
#     account_db_conn = AccountSession()
#     container_list = account_db_conn.query(ContainerInfo). \
#         filter_by(account_name=user_name).all()
#     for container in container_list:
#         container_info_list.append({
#             'container_name': container.container_name,
#             'object_count': container.object_count,
#             'size': container.size,
#             'date_created': container.date_created,
#         })
#     return container_info_list


import random
import time


def strTimeProp(start, end, format, prop):
    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def randomDate(start, end, prop):
    return strTimeProp(start, end, '%m/%d/%Y %I:%M %p', prop)


def get_active_account_clusters_ref(user_name):
    memcache_client = MemcacheClient()
    account_ring = memcache_client.get('ring_account_1')
    if account_ring is None:
        return {
            'result': 'Failed',
            'message': 'account ring is not found'
        }
    account_ring = json.loads(account_ring)
    user_hash = hashlib.md5(user_name)
    partition_pos = int(bin(int(user_hash.hexdigest(), 16))[2:][-account_ring['power_number']:], 2)
    ref_clusters = account_ring['parts'][partition_pos]['cluster_refs']
    active_clusters = []
    for cluster_id in ref_clusters:
        cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
        cluster_status = cluster_info.status
        if cluster_status == SystemCluster.ACTIVE:
            active_clusters.append(cluster_info.name)
    return active_clusters


def get_active_container_clusters_ref(user_name, container_name):
    # global name of this container is user_name.container_name
    container_abs_name = user_name + '.' + container_name
    memcache_client = MemcacheClient()
    container_ring = memcache_client.get('ring_container_1')
    if container_ring is None:
        return {
            'result': 'Failed',
            'message': 'account ring is not found'
        }
    container_ring = json.loads(container_ring)
    container_hash = hashlib.md5(container_abs_name)
    partition_pos = int(bin(int(container_hash.hexdigest(), 16))[2:][-container_ring['power_number']:], 2)
    ref_clusters = container_ring['parts'][partition_pos]['cluster_refs']
    active_clusters = []
    for cluster_id in ref_clusters:
        cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
        cluster_status = cluster_info.status
        if cluster_status == SystemCluster.ACTIVE:
            active_clusters.append(cluster_info.name)
    return active_clusters


def get_active_object_refs(account_name, container_name, object_name, option_ring_name):
    active_clusters = []
    # global name of this container is user_name.container_name
    # container_abs_name = user_name + '.' + container_name
    # memcache_client = MemcacheClient()
    # container_ring = memcache_client.get('ring_container_1')
    # if container_ring is None:
    #     return {
    #         'result': 'Failed',
    #         'message': 'account ring is not found'
    #     }
    # container_ring = json.loads(container_ring)
    # container_hash = hashlib.md5(container_abs_name)
    # partition_pos = int(bin(int(container_hash.hexdigest(), 16))[2:][-container_ring['power_number']:], 2)
    # ref_clusters = container_ring['parts'][partition_pos]['cluster_refs']
    # active_clusters = []
    # for cluster_id in ref_clusters:
    #     cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
    #     cluster_status = cluster_info.status
    #     if cluster_status == SystemCluster.ACTIVE:
    #         active_clusters.append(cluster_info.name)
    return active_clusters


@app.task(time_limit=5)
def get_container_details(user_name, container_name):
    container_details = None
    account_db_conn = AccountSession()
    container_info = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=user_name, container_name=container_name).first()
    # print(container_info)
    if container_info is not None:
        container_details = {
            'account_name': container_info.account_name,
            'container_name': container_info.container_name,
            'object_count': container_info.object_count,
            'size': container_info.size,
            'date_created': str(container_info.date_created)
        }
    account_db_conn.close()
    return container_details


@app.task(time_limit=5)
def get_object_list(user_name, container_name):
    object_list = []
    container_db_conn = ContainerSession()
    object_info_list = container_db_conn.query(ObjectInfo). \
        filter_by(account_name=user_name, container_name=container_name).all()
    for object_info in object_info_list:
        object_list.append({
            'object_name': object_info.object_name,
            'account_name': object_info.account_name,
            'container_name': object_info.container_name,
            'size': object_info.size,
            'last_update': object_info.last_update,
        })
        container_db_conn.close()
    return object_list


@app.task()
def get_container_info(user_name, container_name):
    active_account_ref = get_active_account_clusters_ref(user_name)
    # print(active_account_ref)
    with allow_join_result():
        container_details = None
        for cluster_name in active_account_ref:
            # print(cluster_name)
            cluster_name = cluster_name
            try:
                get_container_list_task = get_container_details.apply_async(
                    (user_name, container_name),
                    routing_key=cluster_name + '.get_container_list'
                )
                container_details = get_container_list_task.get(timeout=3)
                if container_details is not None:
                    break
                    # print(container_list)
            except Exception as e:
                print ('Failed to retrieval container list from cluster ' + cluster_name)
        if container_details is None:
            return {
                'result': 'failed',
                'message': 'Container ' + user_name + '.' + container_name + " is not found."
            }
        else:
            active_container_refs = get_active_container_clusters_ref(user_name, container_name)
            container_object_list = None
            for cluster_name in active_container_refs:
                print(cluster_name)
                cluster_name = cluster_name
                try:
                    get_object_list_task = get_object_list.apply_async(
                        (user_name, container_name),
                        routing_key=cluster_name + '.get_object_list'
                    )
                    container_object_list = get_object_list_task.get(timeout=3)
                    if container_object_list is not None:
                        break
                        # print(container_list)
                except Exception as e:
                    print ('Failed to retrieval container list from cluster ' + cluster_name)
            if container_object_list is None:
                return {
                    'result': 'failed',
                    'message': 'Failed to retrieval object list from container clusters .'
                }
            else:
                container_details['object_list'] = container_object_list
                return {
                    'result': 'success',
                    'container_info': container_details
                }


@app.task()
def api_get_object_list(user_name, container_name):
    with allow_join_result():
        active_container_refs = get_active_container_clusters_ref(user_name, container_name)
        container_object_list = None
        for cluster_name in active_container_refs:
            # print(cluster_name)
            cluster_name = cluster_name
            try:
                get_object_list_task = get_object_list.apply_async(
                    (user_name, container_name),
                    routing_key=cluster_name + '.get_object_list'
                )
                container_object_list = get_object_list_task.get(timeout=3)
                if container_object_list is not None:
                    break
            except Exception as e:
                print ('Failed to retrieval container list from cluster ' + cluster_name)
        return container_object_list


@app.task()
def api_create_object(user_name, container_name, object_file_name, file_data, option_name, file_size):
    with allow_join_result():
        file_size_limit = 2 * 1024 * 1024

        active_container_refs = get_active_container_clusters_ref(user_name, container_name)
        if option_name == 'economy':
            if file_size> file_size_limit:
                option_ring_name = ''
        elif option_name == 'speed':
            pass
        # active_container_refs = get_active_object_refs(user_name, container_name, option_ring_name)

        # for cluster_info in active_container_refs:
        #     create_container_task = create_container.apply_async(
        #         (user_name, container_name),
        #         routing_key=cluster_name + '.create_container'
        #     )
        #     is_created = create_container_task.get(timeout=3)
        #     if is_created:
        #         break
        #
        # if is_created:
        #     return {
        #         'is_created': True,
        #         'message': 'new container is created'
        #     }
        # else:
        #     return {
        #         'is_created': False,
        #         'message': 'Container already exists or failed to connect to Container Clusters'
        #     }
        #     # return None



def get_active_container_clusters_ref(user_name, container_name):
    # global name of this container is user_name.container_name
    container_abs_name = user_name + '.' + container_name
    memcache_client = MemcacheClient()
    container_ring = memcache_client.get('ring_container_1')
    if container_ring is None:
        return {
            'result': 'Failed',
            'message': 'account ring is not found'
        }
    container_ring = json.loads(container_ring)
    container_hash = hashlib.md5(container_abs_name)
    partition_pos = int(bin(int(container_hash.hexdigest(), 16))[2:][-container_ring['power_number']:], 2)
    ref_clusters = container_ring['parts'][partition_pos]['cluster_refs']
    active_clusters = []
    for cluster_id in ref_clusters:
        cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
        cluster_status = cluster_info.status
        if cluster_status == SystemCluster.ACTIVE:
            active_clusters.append(cluster_info.name)
    return active_clusters