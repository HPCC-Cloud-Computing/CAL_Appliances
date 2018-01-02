from __future__ import absolute_import, unicode_literals
# import eventlet
#
# eventlet.monkey_patch()
import os
import sys
import time
import django
from django.utils.timezone import tzinfo
from sys import path
from django.utils import timezone
from os.path import abspath, dirname
import datetime
import requests

path.insert(0, os.getcwd())
from mcos.settings.shared import PERIODIC_SYNCHRONIZE
from mcos.settings.base import TIME_ZONE
from mcos.utils import create_service_connector
from mcos.settings.storage_service_conf import STORAGE_SERVICE_CONFIG, STORAGE_CONTAINER_NAME

SERVICE_TYPE = STORAGE_SERVICE_CONFIG['type']
AUTH_INFO = STORAGE_SERVICE_CONFIG['auth_info']

from mcos_resolver_and_ring_server import tasks


# for path_name in path:
#     print path_name

def setup_django_db_context(db_setting_modules):
    os.environ['DJANGO_SETTINGS_MODULE'] = db_setting_modules
    django.setup()


setup_django_db_context(db_setting_modules='mcos.settings')
from mcos.apps.admin.system.models import SystemCluster
from mcos.apps.admin.system.models import ObjectServiceInfo


# sync container row in container info table

def send_sync_container_msg(check_container, ref_cluster):
    cluster_url = 'http://' + ref_cluster['address_ip'] + ":" + ref_cluster['address_port']
    # print('check replica in cluster ' + cluster_url)
    target_url = cluster_url + '/file-and-container/sync/sync-container-row/'
    try:
        requests.post(target_url, data=check_container, timeout=3)
    except Exception as e:
        pass


def sync_container_row(check_container):
    # print('synchronize for container ' +
    #       check_container['account_name'] + '.' + check_container['container_name'])
    check_time_stamp = datetime.datetime.strptime(
        check_container['time_stamp'], '%Y-%m-%dT%H:%M:%S.%f')
    # get last_update from other clusters
    ref_clusters = tasks.get_account_clusters_ref.apply_async((check_container['account_name'],))
    ref_clusters = ref_clusters.get()
    for ref_cluster in ref_clusters:
        cluster_url = 'http://' + ref_cluster['address_ip'] + ":" + ref_cluster['address_port']
        # print('check replica in cluster ' + cluster_url)
        target_url = cluster_url + '/file-and-container/sync/get-container-time-stamp/'
        try:
            get_req = requests.get(
                target_url, params={'account_name': check_container['account_name'],
                                    'container_name': check_container['container_name'],
                                    }, timeout=5)
            status_code = get_req.status_code
            if status_code == 200:
                resp_data = get_req.json()
                if resp_data['result'] == 'success':
                    if resp_data['is_exist'] == 'true':
                        target_time_stamp = datetime.datetime.strptime(
                            resp_data['time_stamp'], '%Y-%m-%dT%H:%M:%S.%f')
                        if check_time_stamp > target_time_stamp:
                            send_sync_container_msg(check_container, ref_cluster)
                    else:
                        send_sync_container_msg(check_container, ref_cluster)
        except Exception as e:
            pass


def account_db_sync():
    container_list_task = tasks.sync_get_container_list.apply_async()
    container_list = container_list_task.get()
    for container in container_list:
        sync_container_row(container)
        # break


# sync object row in container information
def send_sync_object_info_msg(check_object, ref_cluster):
    cluster_url = 'http://' + ref_cluster['address_ip'] + ":" + ref_cluster['address_port']
    target_url = cluster_url + '/file-and-container/sync/sync-object-row/'
    try:
        requests.post(target_url, data=check_object, timeout=3)
    except Exception as e:
        pass


def sync_object_row(check_object):
    check_time_stamp = datetime.datetime.strptime(
        check_object['time_stamp'], '%Y-%m-%dT%H:%M:%S.%f')
    # get last_update from other clusters
    ref_clusters = tasks.get_container_clusters_ref.apply_async(
        (check_object['account_name'], check_object['container_name']))
    ref_clusters = ref_clusters.get()
    for ref_cluster in ref_clusters:
        cluster_url = 'http://' + ref_cluster['address_ip'] + ":" + ref_cluster['address_port']
        target_url = cluster_url + '/file-and-container/sync/get-object-time-stamp/'
        try:
            get_req = requests.get(
                target_url, params={'account_name': check_object['account_name'],
                                    'container_name': check_object['container_name'],
                                    'object_name': check_object['object_namer']
                                    }, timeout=5)
            status_code = get_req.status_code
            if status_code == 200:
                resp_data = get_req.json()
                if resp_data['result'] == 'success':
                    if resp_data['is_exist'] == 'true':
                        target_time_stamp = datetime.datetime.strptime(
                            resp_data['time_stamp'], '%Y-%m-%dT%H:%M:%S.%f')
                        if check_time_stamp > target_time_stamp:
                            send_sync_object_info_msg(check_object, ref_cluster)
                    else:
                        send_sync_object_info_msg(check_object, ref_cluster)
        except Exception as e:
            pass


def container_db_sync():
    pass
    object_list_task = tasks.sync_get_object_list.apply_async()
    object_list = object_list_task.get()
    for object_info in object_list:
        sync_object_row(object_info)
        # break


# sync resolver info row

def send_sync_resolver_info_msg(check_resolver_info, ref_cluster):
    cluster_url = 'http://' + ref_cluster['address_ip'] + ":" + ref_cluster['address_port']
    target_url = cluster_url + '/file-and-container/sync/sync-resolver-info-row/'
    try:
        requests.post(target_url, data=check_resolver_info, timeout=3)
    except Exception as e:
        pass


def sync_resolver_info_row(check_resolver_info):
    check_time_stamp = datetime.datetime.strptime(
        check_resolver_info['time_stamp'], '%Y-%m-%dT%H:%M:%S.%f')
    # get last_update from other clusters
    ref_clusters = tasks.get_resolver_clusters_ref.apply_async(
        (check_resolver_info['account_name'],
         check_resolver_info['container_name'],
         check_resolver_info['object_name']))
    ref_clusters = ref_clusters.get()
    for ref_cluster in ref_clusters:
        cluster_url = 'http://' + ref_cluster['address_ip'] + ":" + ref_cluster['address_port']
        target_url = cluster_url + '/file-and-container/sync/get-resolver-info-time-stamp/'
        try:
            get_req = requests.get(
                target_url, params={'account_name': check_resolver_info['account_name'],
                                    'container_name': check_resolver_info['container_name'],
                                    'object_name': check_resolver_info['object_namer']
                                    }, timeout=5)
            status_code = get_req.status_code
            if status_code == 200:
                resp_data = get_req.json()
                if resp_data['result'] == 'success':
                    if resp_data['is_exist'] == 'true':
                        target_time_stamp = datetime.datetime.strptime(
                            resp_data['time_stamp'], '%Y-%m-%dT%H:%M:%S.%f')
                        if check_time_stamp > target_time_stamp:
                            send_sync_resolver_info_msg(check_resolver_info, ref_cluster)
                    else:
                        send_sync_resolver_info_msg(check_resolver_info, ref_cluster)
        except Exception as e:
            pass


def resolver_db_sync():
    resolver_list_task = tasks.sync_get_resolver_info_list.apply_async()
    resolver_list = resolver_list_task.get()
    for resolver_info in resolver_list:
        sync_resolver_info_row(resolver_info)
        # break


# sync object data
def send_sync_object_data_msg(object_info_metadata, storage_object_name, ref_cluster):
    print ('send request')
    print (object_info_metadata)
    print (storage_object_name)
    print (ref_cluster)
    service_connector = \
        create_service_connector(SERVICE_TYPE, AUTH_INFO)
    object_data = service_connector.download_object(
        STORAGE_CONTAINER_NAME, storage_object_name)
    object_data = object_data[1]
    # print(object_data)
    cluster_url = 'http://' + ref_cluster['address_ip'] + ":" + ref_cluster['address_port']
    print(cluster_url)
    target_url = cluster_url + '/file-and-container/sync/sync-object-data/'
    try:
        requests.post(target_url,
                      data=object_info_metadata,
                      files={'file': object_data},
                      timeout=10)
    except Exception as e:
        pass


def sync_object_data(object_info_metadata, storage_object_name):
    # print(object_info_metadata)
    # print(storage_object_name)
    check_time_stamp = datetime.datetime.strptime(
        object_info_metadata['time_stamp'], '%Y-%m-%d %H:%M:%S.%f')

    option_name = object_info_metadata['option_name']
    ref_clusters = tasks.get_object_cluster_refs.apply_async(
        (object_info_metadata['account_name'],
         object_info_metadata['container_name'],
         object_info_metadata['object_name'],
         option_name))
    ref_clusters = ref_clusters.get()
    # print(check_time_stamp)
    for ref_cluster in ref_clusters:
        cluster_url = 'http://' + ref_cluster['address_ip'] + ":" + ref_cluster['address_port']
        target_url = cluster_url + '/file-and-container/sync/get-object-data-time-stamp/'
        try:
            get_req = requests.get(
                target_url, params={'account_name': object_info_metadata['account_name'],
                                    'container_name': object_info_metadata['container_name'],
                                    'object_name': object_info_metadata['object_name']
                                    }, timeout=5)
            status_code = get_req.status_code
            if status_code == 200:
                resp_data = get_req.json()
                if resp_data['result'] == 'success':
                    if resp_data['is_exist'] == 'true':
                        target_time_stamp = datetime.datetime.strptime(
                            resp_data['time_stamp'], '%Y-%m-%d %H:%M:%S.%f')
                        # print(target_time_stamp)
                        if check_time_stamp > target_time_stamp:
                            send_sync_object_data_msg(
                                object_info_metadata, storage_object_name, ref_cluster)
                    else:
                        send_sync_object_data_msg(
                            object_info_metadata, storage_object_name, ref_cluster)
        except Exception as e:
            print(e)
            pass


def get_object_info(service_connector, obj_storage_name):
    uploaded_object_stat = \
        service_connector.stat_object(STORAGE_CONTAINER_NAME, obj_storage_name)
    object_info = {}
    if SERVICE_TYPE == 'swift':
        object_info = {
            'container_name': uploaded_object_stat['x-object-meta-container.name'],
            'account_name': uploaded_object_stat['x-object-meta-account.name'],
            'object_name': uploaded_object_stat['x-object-meta-object.name'],
            'option_name': uploaded_object_stat['x-object-meta-option.name'],
            'last_update': uploaded_object_stat['x-object-meta-last.update'],
            'time_stamp': uploaded_object_stat['x-object-meta-time.stamp'],
            'is_deleted': uploaded_object_stat['x-object-meta-is.deleted'],
            'file_size': uploaded_object_stat['content-length']  # in byte

        }
    elif SERVICE_TYPE == 'amazon_s3':
        object_info = {
            'container_name': uploaded_object_stat['Metadata']['x-amz-container.name'],
            'account_name': uploaded_object_stat['Metadata']['x-amz-account.name'],
            'object_name': uploaded_object_stat['Metadata']['x-amz-object.name'],
            'option_name': uploaded_object_stat['Metadata']['x-amz-option.name'],
            'last_update': uploaded_object_stat['Metadata']['x-amz-last.update'],
            'time_stamp': uploaded_object_stat['Metadata']['x-amz-time.stamp'],
            'is_deleted': uploaded_object_stat['Metadata']['x-amz-is.deleted'],
            'file_size': uploaded_object_stat['ContentLength']

        }
    return object_info


def object_data_sync():
    service_connector = \
        create_service_connector(SERVICE_TYPE, AUTH_INFO)
    object_data_list = service_connector.list_container_objects(STORAGE_CONTAINER_NAME, '', '')
    object_list = []
    if SERVICE_TYPE == 'swift':
        for object_info in object_data_list:
            object_list.append(object_info['name'])
    elif SERVICE_TYPE == 'amazon_s3':
        for object_info in object_data_list['Contents']:
            object_list.append(object_info['Key'])
    # print (object_data_list) .list_container_objects(container_test, '', '')
    for object_info in object_list:
        storage_object_name = object_info
        object_info_metadata = get_object_info(service_connector,storage_object_name)
        sync_object_data(object_info_metadata, storage_object_name)


while True:
    try:
        account_db_sync()
        container_db_sync()
        resolver_db_sync()
        object_data_sync()
        time.sleep(PERIODIC_SYNCHRONIZE)

    except Exception as e:
        print(e)
        time.sleep(PERIODIC_SYNCHRONIZE)
        # sys.exit(1)
