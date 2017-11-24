from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

import views

urls = [
    url(r'^container-list', views.get_container_list, name='container_list'),
    url(r'^container-info', views.get_container_info, name='container_info'),
    url(r'^create-container', views.create_container, name='create_container'),
    url(r'^upload-file', views.upload_file, name='upload_file')


]
urlpatterns = urls
