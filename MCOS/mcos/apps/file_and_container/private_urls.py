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
        url(r'^delete-container/$',
            private_views.delete_container, name='delete-container'),

        url(r'^update-container-info/$',
            private_views.update_container_info, name='update_container_info'),

        url(r'^update-object-info/$',
            private_views.update_object_info, name='update_object_info'),

        url(r'^update-resolver-info/$',
            private_views.update_resolver_info, name='update_resolver_info'),

        url(r'^upload-object-data/$',
            private_views.upload_object_data, name='update_object_data'),

        url(r'^delete-object-data/$',
            private_views.delete_object_data, name='delete_object_data'),

        url(r'^get-object-option/$',
            private_views.get_resolver_info, name='get_object_option'),

        url(r'^get-object-info/$',
            private_views.get_object_info, name='get_object_info'),
        url(r'^download-object/$',
            private_views.download_object, name='download_object'),
    ]
urlpatterns = urls + static(settings.MEDIA_URL,
                            document_root=settings.MEDIA_ROOT)
