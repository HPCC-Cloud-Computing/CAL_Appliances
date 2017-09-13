from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models
import uuid


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
    # node address - ip+port
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


# from . import utils.from . import utils
class SystemNode(models.Model):
    class Meta:
        db_table = 'system_node'
        app_label = 'admin'

    # ACTIVE
    # SHUTOFF
    # DISCONNECTED
    ACTIVE = 1
    SHUTOFF = 2
    DISCONNECTED = 3
    CLOUD_SERVICE_DISCONNECTED = 4
    STATUS = (
        (ACTIVE, 'ACTIVE'),
        (SHUTOFF, 'SHUTOFF'),
        (DISCONNECTED, 'DISCONNECTED'),
        (CLOUD_SERVICE_DISCONNECTED, 'CLOUD_SERVICE_DISCONNECTED')
    )
    # uuid
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # node name
    name = models.CharField('name', max_length=255, unique=True)
    # service_info
    service_info = models.OneToOneField(ObjectServiceInfo,
                                        on_delete=models.CASCADE,
                                        related_name='system_node')
    # node status
    status = models.IntegerField(choices=STATUS, default=ACTIVE)
