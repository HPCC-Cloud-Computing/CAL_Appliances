import os
import sys
import django
import json
import socket
import uuid
import requests
from sys import path
from optparse import OptionParser
from os.path import abspath, dirname
from calplus.client import Client
from calplus.provider import Provider
from django.core.wsgi import get_wsgi_application
import utils
from mcos.settings.storage_service_conf import STORAGE_SERVICE_CONFIG, \
    TEST_CONTAINER_NAME, TEST_OBJECT_NAME, TEST_FILE_PATH
from mcos.settings.mcos_conf import MCOS_IP, MCOS_PORT, CONNECT_SERVER, \
    MCOS_CLUSTER_NAME

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
        try:
            create_and_check_service_connection(service_type, auth_info)
            check_storage_service_specs(service_specs)
        except CheckStorageServiceError as e:
            raise CheckStorageServiceError(e.message)

        if len(SystemCluster.objects.filter(
                name=MCOS_CLUSTER_NAME).all()) == 0:
            if CONNECT_SERVER == 'localhost':
                cluster_id = local_setup(SystemCluster, ObjectServiceInfo)
            else:
                cluster_id = remote_setup(CONNECT_SERVER, SystemCluster,
                                          ObjectServiceInfo)

            SYSTEM_INFO['current_cluster_id'] = cluster_id
        else:
            current_cluster = SystemCluster.objects.filter(
                name=MCOS_CLUSTER_NAME).first()
            SYSTEM_INFO['current_cluster_id'] = str(current_cluster.id)
    except Exception as e:
        print e.message
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


def login_cluster(session, cluster_url, user_name, password):
    try:
        login_url = cluster_url + "auth/api_login/"
        session.get(login_url)
        csrftoken = session.cookies['csrftoken']
        login_resp = session.post(login_url,
                                  data={'csrfmiddlewaretoken': csrftoken,
                                        'user_name_email': user_name,
                                        'password': password},
                                  timeout=20)
        # check if login is success or not
        if login_resp.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False


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
    # second, connect to remote server in config file
    # to try to add this cluster to system
    # last, retrieve cluster list from remote server and add this to database
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
    # send request to remote cluster
    try:
        session = requests.Session()
        cluster_url = "http://" + CONNECT_SERVER + "/"
        is_login = login_cluster(session, cluster_url, 'admin', 'bkcloud')
        if is_login:
            try:
                retry_connect = True
                while retry_connect:
                    remote_connect_to_system_url = \
                        cluster_url + "admin/system/remote_connect_to_system/"
                    csrftoken = session.cookies['csrftoken']
                    resp = session.post(
                        remote_connect_to_system_url,
                        data={
                            'csrfmiddlewaretoken': csrftoken,
                            'cluster_id': cluster_id,
                            # 'cluster_id': '77c2e72f7a9d42c6894c6b3caac06197',
                            'cluster_name': cluster_name,
                            'cluster_ip': address_ip,
                            'cluster_port': address_port,
                            'service_info': service_info
                        },
                        timeout=125
                    )
                    status_code = resp.status_code
                    if status_code == 200:
                        resp_data = resp.json()
                        if resp_data['is_connected_to_system'] == 'true':
                            cluster_list = resp_data['cluster_list']
                            for cluster_info in cluster_list:
                                # add cluster_info to database
                                add_cluster_info_to_database(cluster_info,
                                                             SystemCluster,
                                                             ObjectServiceInfo)
                            return cluster_id
                        else:
                            # resp_data['is_connected_to_system'] == 'false'
                            raise SystemConnectionError(
                                "Failed to remote setup. "
                                "Reason: System Reject remote setup"
                                "at this time or an error has been occur. "
                                "Try again later.")
                    else:
                        raise SystemConnectionError(
                            "An Error has been occurred. "
                            "Cannot setup remote setup for "
                            "this cluster.")
            except Exception as e:
                raise SystemConnectionError("An Error has been occurred. "
                                            "Cannot setup remote setup for "
                                            "this cluster.")
        else:
            raise SystemConnectionError("An Error has been occurred. "
                                        "Cannot login to remote server for "
                                        "remote setup this cluster.")
        session.close()
    except Exception as e:
        raise SystemConnectionError("An Error has been occurred. "
                                    "Cannot connect to remote server for "
                                    "remote setup this cluster.")


def create_and_check_service_connection(service_type, access_info):
    # first, create service connector.
    service_connector = \
        utils.create_service_connector(service_type, access_info)
    try:
        # create test_container, upload test object then delete its
        service_connector.create_container(TEST_CONTAINER_NAME)
        container_list = service_connector.driver.list_containers()
        test_container_created = False
        for container_info in container_list:
            if container_info['name'] == TEST_CONTAINER_NAME:
                test_container_created = True
        if test_container_created is False:
            raise CheckStorageServiceError("Storage Service Checking Failed."
                                           " Cannot Create Container.")

        print("Check create container successful.")
        with open(TEST_FILE_PATH, 'r') \
                as sample_file_content:
            service_connector.upload_object(obj=TEST_OBJECT_NAME,
                                            container=TEST_CONTAINER_NAME,
                                            contents=sample_file_content)
            test_object_length = os.path.getsize(TEST_FILE_PATH)
            uploaded_object_stat = service_connector.stat_object(
                TEST_CONTAINER_NAME, TEST_OBJECT_NAME)
            download_test_object_content = service_connector.download_object(
                TEST_CONTAINER_NAME, TEST_OBJECT_NAME)
            if int(test_object_length) != \
                    int(uploaded_object_stat['content-length']) \
                    or int(test_object_length) != \
                            int(download_test_object_content[0]
                                ['content-length']):
                raise CheckStorageServiceError('Create test object failed.')
        print("Check create test object successful.")
        service_connector.delete_object(TEST_CONTAINER_NAME, TEST_OBJECT_NAME)
        service_connector.delete_container(TEST_CONTAINER_NAME)
        print('Checking service connection complete. No problem found.')
    except Exception as e:
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

