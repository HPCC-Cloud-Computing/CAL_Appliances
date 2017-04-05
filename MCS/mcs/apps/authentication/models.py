from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    class Meta:
        db_table = 'userprofile'
        app_label = 'authentication'

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    company = models.CharField(default='HUST', max_length=50)
    image = models.ImageField(upload_to='avatars',
                              default='avatars/avatar.png',
                              blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
