from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from . import views

urls = \
    [
        url(r'^$',
            views.dashboard_overview, name='dashboard_overview'),
        url(r'^cluster_management/$',
            views.cluster_management, name='cluster_management'),
        url(r'^core_ring/$',
            views.core_ring, name='core_ring'),
        url(r'^options_management/$',
            views.options_management, name='options_management'),
        url(r'^home/$',
            views.test_user_role, name='home'),
        url(r'^clusters_tbl_api/$', views.clusters_tbl_api,
            name='clusters_tbl_api'),
        url(r'^clusters_info_api/$', views.clusters_tbl_api,
            name='clusters_info_api'),
        url(r'^get_clusters_ids/', views.get_clusters_ids,
            name='get_clusters_ids'),
        url(r'^get_ring_clusters/', views.get_ring_clusters,
            name='get_ring_clusters')
    ]

urlpatterns = urls
# urlpatterns = urls + static(settings.MEDIA_URL,
#                             document_root=settings.MEDIA_ROOT)
