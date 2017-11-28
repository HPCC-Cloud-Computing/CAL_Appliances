from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from . import private_api_views as private_views

urls = \
    [
        # url(r'^get_csrf_token', views.get_csrf_token, name='get_csrf_token'),
        url(r'^container-list/$',
            private_views.get_container_list, name='get_container_list'),
        url(r'^container-details/$',
            private_views.get_container_details, name='get_container_details'),
        url(r'^container-object-list/$',
            private_views.get_container_object_list, name='get_container_object_list'),
        url(r'^create-container/$',
            private_views.create_container, name='create-container'),
    ]
urlpatterns = urls + static(settings.MEDIA_URL,
                            document_root=settings.MEDIA_ROOT)
