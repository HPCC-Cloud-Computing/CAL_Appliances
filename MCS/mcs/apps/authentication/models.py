from __future__ import unicode_literals
import os

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

CURRENT_DIR = os.path.dirname(__file__)
IMG_DIR = os.path.join(CURRENT_DIR, 'static/assets/img/')


class UserProfile(models.Model):
    class Meta:
        db_table = 'userprofile'
        app_label = 'authentication'

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    company = models.CharField(default='HUST', max_length=50)
    image = models.ImageField()
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
