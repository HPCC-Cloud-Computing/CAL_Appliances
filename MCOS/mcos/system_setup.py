import os
import sys
import django
import json
import socket
import uuid
import requests
import memcache
from sys import path
from optparse import OptionParser
from os.path import abspath, dirname
from calplus.client import Client
from calplus.provider import Provider
from django.db import ProgrammingError
from utils import *
from mcos.settings.storage_service_conf import STORAGE_SERVICE_CONFIG, \
    TEST_CONTAINER_NAME, TEST_OBJECT_NAME, TEST_FILE_PATH, \
    STORAGE_CONTAINER_NAME
from mcos.settings.mcos_conf import MCOS_IP, MCOS_PORT, CONNECT_SERVER, \
    MCOS_CLUSTER_NAME
from mcos.settings import MEMCACHED_IP, MEMCACHED_PORT
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient

SITE_ROOT = dirname(dirname(abspath(__file__)))

path.insert(0, SITE_ROOT)


def setup_django_db_context(db_setting_modules):
    os.environ['DJANGO_SETTINGS_MODULE'] = db_setting_modules
    django.setup()


class SystemConnectionError(Exception):
    pass


class CheckStorageServiceError(Exception):
    pass


def connect_to_system(db_setting_modules, SYSTEM_INFO):
    try:
        setup_django_db_context(db_setting_modules)

        from mcos.apps.admin.system.models import SystemCluster
        from mcos.apps.admin.system.models import ObjectServiceInfo
        service_type = STORAGE_SERVICE_CONFIG['type']
        auth_info = STORAGE_SERVICE_CONFIG['auth_info']
        service_specs = STORAGE_SERVICE_CONFIG['specifications']
        memcache_client = memcache.Client([(MEMCACHED_IP, MEMCACHED_PORT)])
        try:
            check_service_connection(service_type, auth_info)
            check_storage_service_specs(service_specs)
            create_storage_container(service_type, auth_info)
        except CheckStorageServiceError as e:
            raise CheckStorageServiceError(e.message)

        if len(SystemCluster.objects.filter(
                name=MCOS_CLUSTER_NAME).all()) == 0:
            if set_lock('cluster_setup_pid') is True:
                if CONNECT_SERVER == 'localhost':
                    cluster_id = local_setup(SystemCluster, ObjectServiceInfo)
                else:
                    cluster_id = remote_setup(CONNECT_SERVER, SystemCluster,
                                              ObjectServiceInfo)
                release_lock('cluster_setup_pid')
                memcache_client.set('current_cluster_id', cluster_id)
            else:
                raise SystemConnectionError(
                    "Failed to setup cluster, another process is hold setup"
                    "cluster lock. Try again later.")
        else:
            current_cluster = SystemCluster.objects.filter(
                name=MCOS_CLUSTER_NAME).first()
            memcache_client.set('current_cluster_id', str(current_cluster.id))
    except ProgrammingError:
        raise SystemConnectionError(
            "Failed to setup database, check config again.")
    except Exception as e:
        print(e.message)
        raise SystemConnectionError(e.message)


# local setup for first cluster in system

# connect to Object Storage Services check connection
# assumes connections is OK

# step 1: Use CAL to connect with Object Storage Service and
# get these information which CAL can serve (capacity)
# step 2: write a benchmark tool to test network
# or disk performance of current Object Storage Service
#
def local_setup(SystemCluster, ObjectServiceInfo):
    service_type = STORAGE_SERVICE_CONFIG['type']
    auth_info = STORAGE_SERVICE_CONFIG['auth_info']
    service_specs = STORAGE_SERVICE_CONFIG['specifications']
    # check if cluster info is not exist, Create First System Cluster
    if len(SystemCluster.objects.filter(
            name=MCOS_CLUSTER_NAME).all()) == 0:
        current_cluster_id = str(uuid.uuid4())
        service_id = str(uuid.uuid4())
        service_info = ObjectServiceInfo.create_service_info_data(
            service_id, service_type, auth_info, service_specs)
        service_info.save()
        first_system_cluster = SystemCluster(
            id=current_cluster_id,
            name=MCOS_CLUSTER_NAME,
            address_ip=MCOS_IP,
            address_port=MCOS_PORT,
            service_info=service_info
        )
        # setup distance info
        # distance from a cluster to itself is 1
        first_cluster_distance_info = json.dumps({MCOS_CLUSTER_NAME: '-1'})
        first_system_cluster.service_info.distance_info = \
            first_cluster_distance_info
        first_system_cluster.service_info.save()
        first_system_cluster.save()
    current_cluster_info = SystemCluster.objects.filter(
        name=MCOS_CLUSTER_NAME).first()
    return str(current_cluster_info.id)


def add_cluster_info_to_database(cluster_info_dict, SystemCluster,
                                 ObjectServiceInfo):
    cluster_service = ObjectServiceInfo.create_service_info_data(
        service_id=cluster_info_dict['service_info']['id'],
        service_type_input=cluster_info_dict['service_info']['service_type'],
        auth_info_input=cluster_info_dict['service_info']['auth_info'],
        service_specs_input=cluster_info_dict['service_info'][
            'specifications'],
    )
    cluster = SystemCluster(
        id=cluster_info_dict['id'],
        name=cluster_info_dict['name'],
        address_ip=cluster_info_dict['address_ip'],
        address_port=cluster_info_dict['address_port'],
        service_info=cluster_service
    )
    cluster_service.save()
    cluster.save()


def remote_setup(connect_server, SystemCluster, ObjectServiceInfo):
    service_type = STORAGE_SERVICE_CONFIG['type']
    auth_info = STORAGE_SERVICE_CONFIG['auth_info']
    service_specs = STORAGE_SERVICE_CONFIG['specifications']
    cluster_id = str(uuid.uuid4())
    cluster_name = MCOS_CLUSTER_NAME
    address_ip = MCOS_IP
    address_port = MCOS_PORT
    service_info = json.dumps({
        'id': str(uuid.uuid4()),
        'type': service_type,
        'specifications': service_specs,
        'auth_info': auth_info,
    })
    try:
        cluster_url = "http://" + connect_server + "/"
        get_csrf_token_url = cluster_url + \
                             'admin/system/get_csrf_token'
        remote_connect_to_system_url = \
            cluster_url + "admin/system/remote_connect_to_system/"
        mcos_admin_token = \
            KeyStoneClient.create_admin_client().session.get_token()
        session = requests.Session()
        try:
            retry_connect = True
            while retry_connect:
                req_headers = {'X-Auth-Token': mcos_admin_token}
                csrftoken = session.get(
                    url=get_csrf_token_url,
                    headers=req_headers
                ).json()['csrftoken']
                system_connect_resp = session.post(
                    remote_connect_to_system_url,
                    headers=req_headers,
                    data={
                        'csrfmiddlewaretoken': csrftoken,
                        'cluster_id': cluster_id,
                        'cluster_name': cluster_name,
                        'cluster_ip': address_ip,
                        'cluster_port': address_port,
                        'service_info': service_info
                    },
                    timeout=125
                )
                status_code = system_connect_resp.status_code
                if status_code == 200:
                    resp_data = system_connect_resp.json()
                    if resp_data['is_connected_to_system'] == 'true':
                        cluster_list = resp_data['cluster_list']
                        for cluster_info in cluster_list:
                            add_cluster_info_to_database(cluster_info,
                                                         SystemCluster,
                                                         ObjectServiceInfo)
                        return cluster_id
                    else:
                        raise SystemConnectionError(
                            "Failed to remote setup. "
                            "Reason: System Reject remote setup")
                else:
                    raise SystemConnectionError(
                        "An Error has been occurred when remote setup.")
        except Exception as e:
            print(e.message)
            raise SystemConnectionError(
                "An Error has been occurred when remote setup.")

        session.close()
    except Exception as e:
        print(e.message)
        raise SystemConnectionError("An Error has been occurred. "
                                    "Cannot connect to remote server for "
                                    "remote setup this cluster.")


def check_service_connection(service_type, access_info):
    # first, create service connector.
    service_connector = \
        create_service_connector(service_type, access_info)
    try:
        # create test_container, upload test object then delete its
        service_connector.create_container(TEST_CONTAINER_NAME)
        test_container_created = check_container_is_exist(
            service_connector, TEST_CONTAINER_NAME)
        if test_container_created is False:
            raise CheckStorageServiceError("Storage Service Checking Failed."
                                           " Cannot Create Container.")

        print("Check create container successful.")
        with open(TEST_FILE_PATH, 'rb') \
                as sample_file_content:
            upload_content = sample_file_content.read()
            service_connector.upload_object(
                obj=TEST_OBJECT_NAME,
                container=TEST_CONTAINER_NAME,
                contents=upload_content,
                content_length=len(upload_content),
                metadata={'status': 'UPDATED'}
            )
            test_object_length = os.path.getsize(TEST_FILE_PATH)
            uploaded_object_stat = service_connector.stat_object(
                TEST_CONTAINER_NAME, TEST_OBJECT_NAME)
            download_test_object_content = service_connector.download_object(
                TEST_CONTAINER_NAME, TEST_OBJECT_NAME)
            if STORAGE_SERVICE_CONFIG['type'] == 'swift':
                if int(test_object_length) != \
                        int(uploaded_object_stat['content-length']) \
                        or int(test_object_length) != \
                                int(download_test_object_content[0][
                                        'content-length']):
                    raise CheckStorageServiceError(
                        'Create test object failed.')
            elif STORAGE_SERVICE_CONFIG['type'] == 'amazon_s3':
                if int(test_object_length) != \
                        int(uploaded_object_stat['ContentLength']) \
                        or int(test_object_length) != \
                                int(download_test_object_content[
                                        'ContentLength']):
                    raise CheckStorageServiceError(
                        'Create test object failed.')
        print("Check create test object successful.")
        service_connector.delete_object(TEST_CONTAINER_NAME,
                                        TEST_OBJECT_NAME)
        service_connector.delete_container(TEST_CONTAINER_NAME)
        print('Checking service connection complete. No problem found.')
    except Exception as e:
        print(e.message)
        raise CheckStorageServiceError("Storage Service Checking Failed.")


def check_storage_service_specs(services_specs):
    try:
        if int(services_specs['capacity']) <= 0:
            raise CheckStorageServiceError("invalid capacity value")
        if services_specs['backend-type'] not in ['HDD', 'SSD', 'None']:
            raise CheckStorageServiceError('invalid backend-type, must be'
                                           'HDD or SSD or None')

        if int(services_specs['128k-read']['resp_time']) <= 0 \
                or int(services_specs['128k-read']['op_per_second']) <= 0:
            raise CheckStorageServiceError('invalid 128k-read spec value')

        if int(services_specs['128k-write']['resp_time']) <= 0 \
                or int(services_specs['128k-write']['op_per_second']) <= 0:
            raise CheckStorageServiceError('invalid 128k-write spec value')

        if int(services_specs['10mb-read']['resp_time']) <= 0 \
                or int(services_specs['10mb-read']['op_per_second']) <= 0:
            raise CheckStorageServiceError('invalid 128k-read spec value')

        if int(services_specs['10mb-write']['resp_time']) <= 0 \
                or int(services_specs['10mb-write']['op_per_second']) <= 0:
            raise CheckStorageServiceError('invalid 128k-read spec value')

    except Exception:
        raise CheckStorageServiceError("Invalid Object Storage Service"
                                       "specifications setting.")


def create_storage_container(service_type, access_info):
    # first, create service connector.
    service_connector = \
        create_service_connector(service_type, access_info)
    try:
        storage_container_exist = check_container_is_exist(
            service_connector, STORAGE_CONTAINER_NAME)
        # only create service container if not exist
        if storage_container_exist is False:
            service_connector.create_container(STORAGE_CONTAINER_NAME)
            storage_container_exist = check_container_is_exist(
                service_connector, STORAGE_CONTAINER_NAME)
            if storage_container_exist is False:
                raise CheckStorageServiceError(
                    "Storage Service Checking Failed."
                    " Cannot Create Container.")
        print("Storage container is created.")
    except Exception as e:
        print(e.message)
        raise CheckStorageServiceError("Failed to create storage container.")
