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
# from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME as current_cluster_name
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
from .resolver_db import Session as ResolverSession, ResolverInfo


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


@app.task(time_limit=2)
def get_container_list(account_name):
    container_list = []
    account_db_conn = AccountSession()
    container_list_info = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=account_name, is_deleted=False).all()
    for container in container_list_info:
        container_list.append(container.container_name)
    account_db_conn.close()
    return container_list


@app.task(time_limit=2)
def get_container_details(user_name, container_name):
    container_details = None
    account_db_conn = AccountSession()
    selected_container = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=user_name, container_name=container_name, is_deleted=False).first()
    if selected_container is not None:
        container_details = {
            'account_name': selected_container.account_name,
            'container_name': selected_container.container_name,
            'object_count': selected_container.object_count,
            'size': selected_container.size,
            'date_created': str(selected_container.date_created)
        }
    account_db_conn.close()
    return container_details


@app.task(time_limit=5)
def get_object_list(user_name, container_name):
    # print ('user_name' + user_name)
    # print ('container_name' + container_name)
    object_list = []
    container_db_conn = ContainerSession()
    object_info_list = container_db_conn.query(ObjectInfo). \
        filter_by(account_name=user_name, container_name=container_name, is_deleted=False).all()
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
def get_account_clusters_ref(account_name):
    memcache_client = MemcacheClient()
    account_ring = memcache_client.get('ring_account_1')
    if account_ring is None:
        raise Exception('account ring not found')
    account_ring = json.loads(account_ring)
    user_hash = hashlib.md5(account_name)
    partition_pos = int(bin(int(user_hash.hexdigest(), 16))[2:][-account_ring['power_number']:], 2)
    ref_clusters = account_ring['parts'][partition_pos]['cluster_refs']
    active_clusters = []
    for cluster_id in ref_clusters:
        cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
        cluster_status = cluster_info.status
        if cluster_status == SystemCluster.ACTIVE:
            active_clusters.append({
                'name': cluster_info.name,
                'address_ip': cluster_info.address_ip,
                'address_port': cluster_info.address_port
            })
    return active_clusters


@app.task()
def get_container_clusters_ref(user_name, container_name):
    # global name of this container is user_name.container_name
    container_abs_name = user_name + '.' + container_name
    memcache_client = MemcacheClient()
    container_ring = memcache_client.get('ring_container_1')
    if container_ring is None:
        raise Exception('container ring not found')
    container_ring = json.loads(container_ring)
    container_hash = hashlib.md5(container_abs_name)
    partition_pos = int(bin(int(container_hash.hexdigest(), 16))[2:][-container_ring['power_number']:], 2)
    ref_clusters = container_ring['parts'][partition_pos]['cluster_refs']
    active_clusters = []
    for cluster_id in ref_clusters:
        cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
        cluster_status = cluster_info.status
        if cluster_status == SystemCluster.ACTIVE:
            if cluster_status == SystemCluster.ACTIVE:
                active_clusters.append({
                    'name': cluster_info.name,
                    'address_ip': cluster_info.address_ip,
                    'address_port': cluster_info.address_port
                })
    return active_clusters


@app.task()
def get_resolver_clusters_ref(user_name, container_name, object_name):
    # global name of data object is user_name.container_name.object_name
    object_name_abs = user_name + '.' + container_name + '.' + object_name
    memcache_client = MemcacheClient()
    group_resolver_ring = memcache_client.get('ring_group_resolver_1')
    if group_resolver_ring is None:
        raise Exception('group resolver ring not found')
    group_resolver_ring = json.loads(group_resolver_ring)
    object_hash = hashlib.md5(object_name_abs)
    partition_pos = int(bin(int(object_hash.hexdigest(), 16))[2:][-group_resolver_ring['power_number']:], 2)
    ref_clusters = group_resolver_ring['parts'][partition_pos]['cluster_refs']
    active_clusters = []
    for cluster_id in ref_clusters:
        cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
        cluster_status = cluster_info.status
        if cluster_status == SystemCluster.ACTIVE:
            if cluster_status == SystemCluster.ACTIVE:
                active_clusters.append({
                    'name': cluster_info.name,
                    'address_ip': cluster_info.address_ip,
                    'address_port': cluster_info.address_port
                })
    return active_clusters


@app.task()
def get_object_cluster_refs(user_name, container_name, object_name, option_name):
    # global name of data object is user_name.container_name.object_name
    object_name_abs = user_name + '.' + container_name + '.' + object_name
    memcache_client = MemcacheClient()
    group_resolver_ring = memcache_client.get('ring_' + option_name + '_1')
    if group_resolver_ring is None:
        raise Exception('group resolver ring not found')
    group_resolver_ring = json.loads(group_resolver_ring)
    object_hash = hashlib.md5(object_name_abs)
    partition_pos = int(bin(int(object_hash.hexdigest(), 16))[2:][-group_resolver_ring['power_number']:], 2)
    ref_clusters = group_resolver_ring['parts'][partition_pos]['cluster_refs']
    active_clusters = []
    for cluster_id in ref_clusters:
        cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
        cluster_status = cluster_info.status
        if cluster_status == SystemCluster.ACTIVE:
            if cluster_status == SystemCluster.ACTIVE:
                active_clusters.append({
                    'name': cluster_info.name,
                    'address_ip': cluster_info.address_ip,
                    'address_port': cluster_info.address_port
                })
    return active_clusters


@app.task()
def create_new_container(new_container_info):
    # check if container is already exists
    account_db_conn = AccountSession()
    container_exist_list = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=new_container_info['account_name'],
                  container_name=new_container_info['container_name']).all()
    print (new_container_info['account_name'])
    print (new_container_info['container_name'])
    print(len(container_exist_list))
    if len(container_exist_list) > 0:
        check_container = container_exist_list[0]
        if check_container.is_deleted == False:
            return False
        else:
            try:
                # updated deleted container
                check_container.object_count = new_container_info['object_count']
                check_container.size = new_container_info['size']
                check_container.date_created = datetime.datetime.strptime(
                    new_container_info['date_created'], '%Y-%m-%d %H:%M:%S.%f')
                check_container.time_stamp = datetime.datetime.strptime(
                    new_container_info['date_created'], '%Y-%m-%d %H:%M:%S.%f')
                check_container.is_deleted = False
                account_db_conn.add(check_container)
                account_db_conn.commit()
                account_db_conn.close()
                return True
            except Exception as e:
                print (e)
                account_db_conn.close()
                return False
    try:
        # add new container to database
        new_container = ContainerInfo(
            account_name=new_container_info['account_name'],
            container_name=new_container_info['container_name'],
            object_count=new_container_info['object_count'],
            size=new_container_info['size'],
            date_created=datetime.datetime.strptime(
                new_container_info['date_created'],
                '%Y-%m-%d %H:%M:%S.%f'),
            time_stamp=datetime.datetime.strptime(
                new_container_info['date_created'],
                '%Y-%m-%d %H:%M:%S.%f')
        )
        account_db_conn.add(new_container)
        account_db_conn.commit()
        account_db_conn.close()
        return True
    except Exception as e:
        print (e)
        account_db_conn.close()
        return False


@app.task()
def delete_container(container_info):
    # check if container is already exists
    account_db_conn = AccountSession()
    container_exist_list = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=container_info['account_name'],
                  container_name=container_info['container_name']).all()
    if len(container_exist_list) > 0:
        try:
            # updated deleted container
            check_container = container_exist_list[0]
            check_container.object_count = container_info['object_count']
            check_container.size = container_info['size']
            check_container.date_created = datetime.datetime.strptime(
                container_info['date_created'], '%Y-%m-%d %H:%M:%S.%f')
            check_container.time_stamp = datetime.datetime.strptime(
                container_info['date_created'], '%Y-%m-%d %H:%M:%S.%f')
            check_container.is_deleted = True
            account_db_conn.add(check_container)
            account_db_conn.commit()
            account_db_conn.close()
            return True
        except Exception as e:
            print (e)
            account_db_conn.close()
            return False
    else:
        return False


@app.task()
# param account_name: string, container_name: string,
# new_object_size: float, last_update: time string
def update_container_info(account_name, container_name, new_object_size, last_update, is_deleted):
    account_db_conn = AccountSession()
    update_container = account_db_conn.query(ContainerInfo). \
        filter_by(account_name=account_name,
                  container_name=container_name).first()
    if update_container is None:
        pass
    else:
        if is_deleted is False:
            try:
                # add new container to database
                update_container.object_count = update_container.object_count + 1
                update_container.size = update_container.size + new_object_size
                update_container.time_stamp = datetime.datetime.strptime(
                    last_update, '%Y-%m-%d %H:%M:%S.%f')
                account_db_conn.add(update_container)
                account_db_conn.commit()
                account_db_conn.close()
                return True
            except Exception as e:
                print (e)
                account_db_conn.close()
                return False
        else:
            pass


@app.task()
# param account_name: string, container_name: string,
# new_object_size: float, last_update: time string
def update_object_info(account_name, container_name, object_name, last_update,
                       object_size, is_deleted):
    container_db_conn = ContainerSession()
    update_object = container_db_conn.query(ObjectInfo). \
        filter_by(account_name=account_name,
                  container_name=container_name,
                  object_name=object_name).first()
    if update_object is None:
        try:
            # add new container to database
            new_object_info = ObjectInfo(
                account_name=account_name,
                container_name=container_name,
                object_name=object_name,
                size=object_size,
                last_update=datetime.datetime.strptime(
                    last_update, '%Y-%m-%d %H:%M:%S.%f'),
                time_stamp=datetime.datetime.strptime(
                    last_update, '%Y-%m-%d %H:%M:%S.%f')
            )
            container_db_conn.add(new_object_info)
            container_db_conn.commit()
            container_db_conn.close()
            return True
        except Exception as e:
            print (e)
            container_db_conn.close()
            return False
    else:
        if is_deleted is False:
            pass
        else:
            pass


@app.task()
# param account_name: string, container_name: string,
# new_object_size: float, last_update: time string
def update_resolver_info(account_name, container_name, object_name,
                         option_name, last_update, is_deleted):
    conn = ResolverSession()
    update_resolver = conn.query(ResolverInfo). \
        filter_by(account_name=account_name,
                  container_name=container_name,
                  object_name=object_name).first()
    if update_resolver is None:
        try:
            # add new container to database
            new_resolver_info = ResolverInfo(
                account_name=account_name,
                container_name=container_name,
                object_name=object_name,
                option_name=option_name,
                time_stamp=datetime.datetime.strptime(
                    last_update, '%Y-%m-%d %H:%M:%S.%f')
            )
            conn.add(new_resolver_info)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print (e)
            conn.close()
            return False
    else:
        if is_deleted is False:
            pass
        else:
            pass


@app.task()
# param account_name: string, container_name: string,
# new_object_size: float, last_update: time string
def get_resolver_info(account_name, container_name, object_name):
    conn = ResolverSession()
    resolver_info = conn.query(ResolverInfo). \
        filter_by(account_name=account_name,
                  container_name=container_name,
                  object_name=object_name).first()
    if resolver_info is not None:
        return resolver_info.option_name
    else:
        return None
