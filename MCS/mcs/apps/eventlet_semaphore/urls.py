from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^write/$', views.write_ring_1, name='write'),
    url(r'^read/$', views.read_ring_1, name='read'),
]
