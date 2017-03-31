from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Provider(models.Model):

    class Meta:
        db_table = 'provider'
        app_label = 'management'

    name = models.CharField(max_length=50)
    config = models.TextField()
    description = models.TextField()
    enable = models.PositiveSmallIntegerField(default=0)
    type = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    USERNAME_FIELD = 'name'


class Network(models.Model):

    class Meta:
        db_table = 'network'
        app_label = 'management'

    name = models.CharField(max_length=100)
    description = models.TextField()
    network_id = models.TextField()
    cidr = models.TextField()
    gateway = models.TextField()
    security_group = models.TextField()
    allocation_pools = models.TextField()
    dns_nameservers = models.TextField()
    connect_external = models.PositiveSmallIntegerField(default=0)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)

    USERNAME_FIELD = 'name'

class App(models.Model):

    class Meta:
        db_table = 'app'
        app_label = 'management'

    name = models.CharField(max_length=100)
    description = models.TextField()
    instance_id = models.TextField()
    network_id = models.TextField()
    docker_image = models.TextField()
    ports = models.TextField()
    ip = models.TextField()
    start_script = models.TextField()
    state = models.TextField()
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
