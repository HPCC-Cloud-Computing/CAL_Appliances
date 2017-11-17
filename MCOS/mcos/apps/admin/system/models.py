from __future__ import unicode_literals
import json
import uuid
from django.utils import timezone
from django.db import models


class ObjectServiceInfo(models.Model):
    class Meta:
        db_table = 'cloud_service_info'
        app_label = 'admin'
        # abstract = True

    # ACTIVE
    # SHUTOFF
    # DISCONNECTED
    SWIFT = 1
    AMAZON_S3 = 2
    CEPH = 3
    SERVICE_TYPE = (
        (SWIFT, 'SWIFT'),
        (AMAZON_S3, 'AMAZON_S3'),
        (CEPH, 'CEPH'),
    )
    # uuid
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # cloud service type
    service_type = models.IntegerField(choices=SERVICE_TYPE)
    # cluster address - ip+port
    specifications = models.CharField('specifications',
                                      max_length=1023)

    # # access information: storage service IP Address + Port.
    # Current is not used
    # access_info = models.CharField('access_info',
    #                                max_length=1023)
    # authentication information: storage authentication ( depend cloud service
    # type)
    auth_info = models.CharField('auth_info', max_length=1023)
    distance_info = models.CharField('distance_info',
                                     max_length=1023, blank=True,
                                     default='')

    @staticmethod
    def convert_sv_type_id(service_type_id):
        if service_type_id == 1:
            return 'swift'
        elif service_type_id == 2:
            return 'amazon_s3'
        elif service_type_id == 3:
            return 'ceph'
        else:
            raise Exception("This service type id is not supported")

    @staticmethod
    def create_service_info_data(service_id, service_type_input,
                                 auth_info_input,
                                 service_specs_input):
        service_type = 0
        if service_type_input == 'amazon_s3' or \
                        service_type_input == 'AMAZON_S3':
            service_type = ObjectServiceInfo.AMAZON_S3
        elif service_type_input == 'swift' or \
                        service_type_input == 'SWIFT':
            service_type = ObjectServiceInfo.SWIFT
        elif service_type_input == 'ceph' or \
                        service_type_input == 'CEPH':
            service_type = ObjectServiceInfo.CEPH
        # auth_info = json.dumps(auth_info_input)
        # service_specs = json.dumps(service_specs_input)
        object_storage_service_info = ObjectServiceInfo(
            id=service_id,
            service_type=service_type,
            specifications=service_specs_input,
            auth_info=auth_info_input
        )
        return object_storage_service_info

    def to_dict(self):
        service_info_dict = {
            'id': str(self.id),
            'service_type': ObjectServiceInfo.convert_sv_type_id(
                self.service_type),
            'specifications':
                self.specifications,
            'auth_info':
                self.auth_info,
            'distance_info':
                self.distance_info
        }
        return service_info_dict


# from . import utils.from . import utils
class SystemCluster(models.Model):
    class Meta:
        db_table = 'system_cluster'
        app_label = 'admin'

    # ACTIVE
    # SHUTOFF
    # DISCONNECTED
    ACTIVE = 1
    SHUTOFF = 2
    ERROR = 3
    STATUS = (
        (ACTIVE, 'ACTIVE'),
        (SHUTOFF, 'SHUTOFF'),
        (ERROR, 'ERROR'),
    )
    # uuid
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # cluster name
    name = models.CharField('name', max_length=255, unique=True)
    # cluster address
    address_ip = models.CharField('ip', max_length=255)
    address_port = models.CharField('port', max_length=255)
    # service_info
    service_info = models.OneToOneField(ObjectServiceInfo,
                                        on_delete=models.CASCADE,
                                        related_name='system_cluster')
    # cluster status
    status = models.IntegerField(choices=STATUS, default=ACTIVE)
    last_update = models.DateTimeField('last_update', default=timezone.now)

    def to_dict(self):
        cluster_info_dict = {
            'id': str(self.id),
            'name': self.name,
            'address_ip': self.address_ip,
            'address_port': self.address_port,
            'status': self.status,
            'service_info': self.service_info.to_dict(),
            'last_update': str(self.last_update)
        }
        return cluster_info_dict

# in this function, we don't initialize distance info
