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
        url(r'^home/$',
            views.test_user_role, name='home'),
        url(r'^clusters_tbl_api/$', views.clusters_tbl_api,
            name='clusters_tbl_api')

    ]

urlpatterns = urls
# urlpatterns = urls + static(settings.MEDIA_URL,
#                             document_root=settings.MEDIA_ROOT)
