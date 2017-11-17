from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

import views

urls = [

    url(r'^$',
        views.index, name='index'),
    url(r'^dashboard', views.dashboard, name='dashboard'),
    url(r'^data-management', views.data_management, name='data-management')

]
urlpatterns = urls
