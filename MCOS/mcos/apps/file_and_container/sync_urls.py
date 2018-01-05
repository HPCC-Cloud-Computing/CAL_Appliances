from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from . import sync_views

urls = \
    [
        # url(r'^get_csrf_token', views.get_csrf_token, name='get_csrf_token'),
        url(r'^get-container-time-stamp/$',
            sync_views.get_container_time_stamp, name='get_container_time_stamp'),
        url(r'^sync-container-row/$',
            sync_views.sync_container_row, name='sync_container_row'),
        url(r'^report-container-row/$',
            sync_views.report_container_row, name='report_container_row'),


        url(r'^get-object-info-time-stamp/$',
            sync_views.get_object_info_time_stamp, name='get_object_info_time_stamp'),
        url(r'^sync-object-info-row/$',
            sync_views.sync_object_info_row, name='sync_object_info_row'),

        url(r'^get-resolver-info-time-stamp/$',
            sync_views.get_resolver_info_time_stamp, name='get_resolver_info_time_stamp'),
        url(r'^sync-resolver-info-row/$',
            sync_views.sync_resolver_info_row, name='sync_resolver_info_row'),

        url(r'^get-object-data-time-stamp/$',
            sync_views.get_object_data_time_stamp, name='get_object_data_time_stamp'),
        url(r'^sync-object-data/$',
            sync_views.sync_object_data, name='sync_object_data'),

    ]
urlpatterns = urls + static(settings.MEDIA_URL,
                            document_root=settings.MEDIA_ROOT)
