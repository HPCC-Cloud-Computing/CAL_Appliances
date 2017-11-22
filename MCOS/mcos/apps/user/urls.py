from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

import views

urls = [

    url(r'^$',
        views.index, name='index'),
    url(r'^dashboard', views.dashboard, name='dashboard'),
    url(r'^data-management', views.data_management, name='data-management'),
    url(r'^container-list', views.get_container_list, name='container_list'),
    url(r'^container-info', views.get_container_info, name='container_info')

]
urlpatterns = urls
