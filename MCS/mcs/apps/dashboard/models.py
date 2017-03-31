from __future__ import unicode_literals

from django.db import models


class CloudRing(models.Model):

    class Meta:
        db_table = 'cloudring'
        app_label = 'dashboard'

    identifier = models.CharField(max_length=50)
    USERNAME_FIELD = 'identifier'


class CloudNode(models.Model):

    class Meta:
        db_table = 'cloudnode'
        app_label = 'dashboard'

    identifier = models.CharField(max_length=50)
    config = models.TextField()
    type = models.TextField()
    ring = models.ForeignKey(CloudRing, on_delete=models.CASCADE)

    USERNAME_FIELD = 'identifier'
