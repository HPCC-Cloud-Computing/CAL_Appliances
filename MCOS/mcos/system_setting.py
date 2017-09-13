import os
import sys
import django
import json
import socket
from sys import path
from optparse import OptionParser
from os.path import abspath, dirname
from calplus.client import Client
from calplus.provider import Provider
from django.core.wsgi import get_wsgi_application
import utils
from mcos.settings.storage_service_conf import STORAGE_SERVICE_CONFIG, \
    CONNECT_SERVER, MCOS_SERVICE_NAME, \
    TEST_CONTAINER_NAME, TEST_OBJECT_NAME, TEST_FILE_PATH
from mcos.settings.mcos_conf import MCOS_IP, MCOS_PORT

SITE_ROOT = dirname(dirname(abspath(__file__)))

path.insert(0, SITE_ROOT)


def setup_django_db_context(db_setting_modules):
    os.environ['DJANGO_SETTINGS_MODULE'] = db_setting_modules
    django.setup()


class SystemConnectionError(Exception):
    pass


class CheckStorageServiceError(Exception):
    pass


def connect_to_system(db_setting_modules):
    try:
        setup_django_db_context(db_setting_modules)
        from mcos.apps.admin.system.models import SystemNode
        from mcos.apps.admin.system.models import ObjectServiceInfo
        if CONNECT_SERVER == 'localhost':
            local_setup(SystemNode, ObjectServiceInfo)
        else:
            # remote setup
            remote_setup(CONNECT_SERVER)

            pass

    except Exception as e:
        raise SystemConnectionError(e.message)


# local setup for first node in system

# connect to Object Storage Services check connection
# assumes connections is OK

# step 1: Use CAL to connect with Object Storage Service and
# get these information which CAL can serve (capacity)
# step 2: write a benchmark tool to test network
# or disk performance of current Object Storage Service
#
def local_setup(SystemNode, ObjectServiceInfo):
    service_type = STORAGE_SERVICE_CONFIG['type']
    auth_info = STORAGE_SERVICE_CONFIG['auth_info']
    service_specs = STORAGE_SERVICE_CONFIG['specifications']
    try:
        create_and_check_service_connection(service_type, auth_info)
        check_storage_service_specs(service_specs)
        # if system passed storage service checking
        # check if node info is not exist, Create First System Node
        if len(SystemNode.objects.filter(name=MCOS_SERVICE_NAME).all()) == 0:
            service_info = create_service_info_data(service_type, auth_info,
                                                    service_specs,
                                                    ObjectServiceInfo)
            service_info.save()
            first_system_node = SystemNode(
                name=MCOS_SERVICE_NAME,
                service_info=service_info
            )
            # setup distance info
            # distance from a node to itself is 1
            first_node_distance_info = json.dumps({MCOS_SERVICE_NAME: '1'})
            first_system_node.service_info.distance_info = \
                first_node_distance_info
            first_system_node.service_info.save()
            first_system_node.save()

    except Exception as e:
        raise CheckStorageServiceError(e.message)


def remote_setup(connect_server):
    service_type = STORAGE_SERVICE_CONFIG['type']
    access_info = STORAGE_SERVICE_CONFIG['access_information']
    service_specs = STORAGE_SERVICE_CONFIG['specifications']
    # first, test storage service checking
    try:
        check_storage_service_connection(service_type, access_info)
        check_storage_service_specs(service_specs)
    except CheckStorageServiceError as e:
        raise CheckStorageServiceError(e.message)
    # if system passed storage service checking
    # second, test connection to connect server in config file
    pass


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


# in this function, we don't initialize distance info
def create_service_info_data(service_type_input, auth_info_input,
                             service_specs_input, ObjectServiceInfo):
    service_type = 0
    if service_type_input == 'amazon_s3':
        service_type = ObjectServiceInfo.AMAZON_S3
    elif service_type_input == 'swift':
        service_type = ObjectServiceInfo.SWIFT
    elif service_type_input == 'ceph':
        service_type = ObjectServiceInfo.CEPH
    auth_info = json.dumps(auth_info_input)
    service_specs = json.dumps(service_specs_input)
    object_storage_service_info = ObjectServiceInfo(
        service_type=service_type,
        specifications=service_specs,
        auth_info=auth_info
    )
    return object_storage_service_info
