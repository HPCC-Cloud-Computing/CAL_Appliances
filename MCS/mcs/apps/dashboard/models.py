from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from dashboard import utils


class CloudRing(models.Model):
    class Meta:
        db_table = 'cloudring'
        app_label = 'dashboard'

    owner = models.ForeignKey(User, on_delete=models.CASCADE)


class CloudNode(models.Model):
    class Meta:
        db_table = 'cloudnode'
        app_label = 'dashboard'

    # Define cloudnode's status
    FULL = 1
    OK = 2
    CORRUPTED = 3

    STATUS = (
        (FULL, 'FULL'),
        (OK, 'OK'),
        (CORRUPTED, 'CORRUPTED'),
    )

    config = models.TextField()
    type = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(default=None)
    # Hash from ip_address
    identifier = models.CharField('identifier', max_length=255, null=True)
    status = models.IntegerField(choices=STATUS, blank=True,
                                 null=True, default=OK)
    ring = models.ForeignKey('CloudRing', on_delete=models.CASCADE)

    USERNAME_FIELD = 'identifier'

    def save(self, *args, **kwargs):
        self.identifier = utils.generate_hash_key(str(self.ip_address))
        super(CloudNode, self).save(*args, **kwargs)

    def init_finger_table(self):
        pass

    def init_successor_list(self):
        pass

    def update_successor_list(self):
        pass

    # called periodically. n asks the successor
    # about its predecessor, verifies if n's immediate
    # successor is consistent, and tells the successor about n
    def stabilize(self):
        pass

    # called periodically. refreshes finger table entries.
    # next stores the index of the finger to fix
    def fix_fingers(self):
        pass

    # ask node n to find the successor of id
    def find_successor(self, object_id):
        pass

    # called periodically. checks whether predecessor has failed.
    def check_predecessor(self):
        pass

    # search the local table for the highest predecessor of id
    def closest_preceding_node(self, object_id):
        pass

    def create(self):
        pass

    # join a Chord ring containing node n'.
    def join(self, node_id):
        pass


class FileManager(models.Manager):
    pass


class File(models.Model):
    class Meta:
        db_table = 'file'
        app_label = 'dashboard'

    # File(file only not folder)
    # Update - all replica is updated
    # Not_update - not all replica is updated
    # Available - at least one replica is updated
    # Not available - all replica is not updated
    UPDATE = 1
    NOT_UPDATE = 2
    AVAILABLE = 3
    NOT_AVAILABLE = 4

    STATUS = (
        (UPDATE, 'UPDATE'),
        (NOT_UPDATE, 'NOT_UPDATE'),
        (AVAILABLE, 'AVAILABLE'),
        (NOT_AVAILABLE, 'NOT_AVAILABLE')
    )

    name = models.CharField('name', max_length=255)
    # Hash from name
    identifier = models.CharField('identifier', max_length=255, null=True)
    status = models.IntegerField(choices=STATUS, default=AVAILABLE,
                                 null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    last_modified = models.DateTimeField('last_modified',
                                         auto_now_add=True)
    path = models.CharField('path', null=True, max_length=255)
    # TODO: Change upload_to folder to /tmp/<user_id>/%Y/%m/%d
    content = models.FileField('content', null=True)
    is_folder = models.BooleanField('is_folder',
                                    default=True)
    is_root = models.BooleanField('is_root',
                                  default=False)
    size = models.IntegerField('size', null=True,
                               editable=False)
    parent = models.ForeignKey('self', verbose_name=('parent'),
                               null=True, blank=True,
                               related_name='children')

    objects = FileManager()

    def save(self, *args, **kwargs):
        self.identifier = utils.generate_hash_key(str(self.path))
        super(File, self).save(*args, **kwargs)

    def contains_file(self, folder_name):
        try:
            self.children.get(name=folder_name)
            return True
        except File.DoesNotExist:
            return False


class FileReplica(models.Model):
    class Meta:
        db_table = 'replica'
        app_label = 'dashboard'

    UPDATE = 1
    NOT_UPDATE = 2

    STATUS = (
        (UPDATE, 'UPDATE'),
        (NOT_UPDATE, 'NOT_UPDATE'),
    )

    identifier = models.CharField('identifier', max_length=255, null=True)
    status = models.IntegerField(choices=STATUS, default=NOT_UPDATE,
                                 null=True, blank=True)
