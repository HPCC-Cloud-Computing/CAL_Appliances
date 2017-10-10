# from __future__ import unicode_literals
# import uuid
# from django.contrib.auth.models import User
# from django.db import models
#
#
# class Role(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     role_name = models.CharField(max_length=50, unique=True, blank=False)
#
#     class Meta:
#         db_table = 'role'
#         app_label = 'authentication'
#         permissions = (
#             ("admin_role", "Can access administration dashboard"),
#             ("user_role", "Can access user dashboard")
#         )
#
#
# class UserProfile(models.Model):
#     class Meta:
#         db_table = 'user_profile'
#         app_label = 'authentication'
#
#     user = models.OneToOneField(User,
#                                 on_delete=models.CASCADE,
#                                 related_name='profile',
#                                 primary_key=True)
#     company = models.CharField(max_length=50, blank=False)
#     roles = models.ManyToManyField(Role)
