from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

import views
import private_urls
import sync_urls

urls = [
    url(r'^csrftoken', views.get_csrf_token, name='get_csrftoken'),
    url(r'^container-list', views.get_container_list, name='container_list'),
    url(r'^container-info', views.get_container_info, name='container_info'),
    url(r'^create-container', views.create_container, name='create_container'),
    url(r'^delete-container', views.delete_container, name='delete_container'),

    url(r'^upload-file', views.upload_file, name='upload_file'),
    url(r'^file-info', views.get_file_info, name='file_info'),
    url(r'^update-file', views.update_file, name='update_file'),
    url(r'^download-file', views.download_file, name='download_file'),
    url(r'^delete-file', views.delete_file, name='delete_file'),

    url(r'^create-object', views.upload_file, name='create_object'),
    url(r'^test-file-name/', views.test_file_name, name='test_file_name'),
    url(r'^private/', include(private_urls.urlpatterns,
                              namespace='private')),
    url(r'^sync/', include(sync_urls.urlpatterns,
                           namespace='sync')),
]
urlpatterns = urls
