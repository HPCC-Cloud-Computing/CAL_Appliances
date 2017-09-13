import os
from calplus.client import Client
from calplus.provider import Provider


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
    except Exception:
        raise CreateServiceConnectorError(
            'Cannot create object storage service connector,'
            ' check config again.')
