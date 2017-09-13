from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models

from . import utils


class FileManager(models.Manager):
    pass


class File(models.Model):
    class Meta:
        db_table = 'file'
        app_label = 'user_dashboard'

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
    size_format = models.CharField('size_format', max_length=255, null=True)
    parent = models.ForeignKey('self', verbose_name=('parent'),
                               null=True, blank=True,
                               related_name='children')

    objects = FileManager()

    def save(self, *args, **kwargs):
        self.identifier = utils.generate_hash_key(str(self.path))
        if not self.is_folder:
            self.size_format = utils.sizeof_fmt(self.size)
        super(File, self).save(*args, **kwargs)

    def contains_file(self, folder_name):
        try:
            self.children.get(name=folder_name)
            return True
        except File.DoesNotExist:
            return False
