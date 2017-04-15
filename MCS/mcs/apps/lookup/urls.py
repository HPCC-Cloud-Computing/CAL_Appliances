from django.conf.urls import url

from lookup import views


urlpatterns = [
    url(r'^init_ring/$', views.init_ring,
        name='init_ring'),
]
