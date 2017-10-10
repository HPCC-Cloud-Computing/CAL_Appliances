import os
import memcache
from calplus.client import Client
from calplus.provider import Provider
from mcos.settings import MEMCACHED_IP, MEMCACHED_PORT
from mcos.settings.storage_service_conf import STORAGE_SERVICE_CONFIG, \
    TEST_CONTAINER_NAME, TEST_OBJECT_NAME, TEST_FILE_PATH, \
    STORAGE_CONTAINER_NAME

DEFAULT_LOCK_VALUE = str(os.getpid())


class CreateServiceConnectorError(Exception):
    pass


def create_service_connector(service_type, access_information):
    try:
        cloud_type, cloud_config = None, None
        if service_type == 'amazon_s3':
            cloud_type = 'amazon'
            cloud_config = {
                "address": access_information['address'],
                "aws_access_key_id": access_information['aws_access_key_id'],
                "aws_secret_access_key":
                    access_information['aws_secret_access_key'],
                "region_name": access_information['region_name'],
                "endpoint_url": access_information['endpoint_url']
            }
        elif service_type == 'swift':
            cloud_type = 'openstack'
            cloud_config = {
                'os_auth_url':
                    access_information['os_auth_url'],
                'os_project_name':
                    access_information['os_project_name'],
                'os_username':
                    access_information['os_username'],
                'os_password':
                    access_information['os_password'],
                'os_project_domain_name':
                    access_information['os_project_domain_name'],
                'os_user_domain_name':
                    access_information['os_user_domain_name'],
                'os_identity_api_version':
                    access_information['os_identity_api_version'],
                'os_auth_version':
                    access_information['os_auth_version'],
                'os_swiftclient_version':
                    access_information['os_swiftclient_version'],
            }
        elif service_type == 'ceph':
            raise CreateServiceConnectorError(
                'Ceph is currently not supported')
        if cloud_type is not None and cloud_config is not None:
            # create connector
            provider = Provider(cloud_type, cloud_config)
            client = Client(version='1.0.0', resource='object_storage',
                            provider=provider)
            return client

        else:
            raise CreateServiceConnectorError('Invalid object service config,'
                                              ' check config again.')
    except Exception as e:
        print(e.message)
        raise CreateServiceConnectorError(
            'Cannot create object storage service connector,'
            ' check config again.')


def check_container_is_exist(storage_service_connector, container_name):
    container_exist = False
    if STORAGE_SERVICE_CONFIG['type'] == 'swift':
        container_list = storage_service_connector.driver. \
            list_containers()
        for container_info in container_list:
            if container_info['name'] == container_name:
                container_exist = True
    elif STORAGE_SERVICE_CONFIG['type'] == 'amazon_s3':
        container_list = storage_service_connector.driver. \
            list_containers()['Buckets']
        for container_info in container_list:
            if container_info['Name'] == container_name:
                container_exist = True
    else:
        raise CheckStorageServiceError("Not support storage service type: " +
                                       STORAGE_SERVICE_CONFIG['type'])
    return container_exist


def set_lock(lock_name, lock_value=DEFAULT_LOCK_VALUE):
    memcache_client = memcache.Client([(MEMCACHED_IP, MEMCACHED_PORT)])
    if memcache_client.get(lock_name) is None:
        memcache_client.set(lock_name, lock_value)
        return lock_value == memcache_client.get(lock_name)
    else:
        return False

#
# def check_lock(lock_name):
#     memcache_client = memcache.Client([(MEMCACHED_IP, MEMCACHED_PORT)])
#     if memcache_client.get(lock_name) is None:
#         return False
#     else:
#         return True


def get_shared_value(key_name):
    memcache_client = memcache.Client([(MEMCACHED_IP, MEMCACHED_PORT)])
    return memcache_client.get(key_name)


def release_lock(lock_name):
    memcache_client = memcache.Client([(MEMCACHED_IP, MEMCACHED_PORT)])
    memcache_client.delete(lock_name)
