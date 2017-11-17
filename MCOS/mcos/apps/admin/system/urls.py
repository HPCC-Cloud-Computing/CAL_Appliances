from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from . import views

urls = \
    [
        url(r'^get_csrf_token', views.get_csrf_token, name='get_csrf_token'),
        url(r'^cluster_list/$',views.get_cluster_list, name='cluster_list'),
        url(r'^remote_connect_to_system/',
            views.remote_connect_to_system,
            name='remote_connect_to_system'),
        url(r'^get_add_cluster_permission/',
            views.get_add_cluster_permission,
            name='get_add_cluster_permission'),
        url(r'^add_new_cluster/',
            views.add_new_cluster,
            name='add_new_cluster'),
        url(r'^release_add_cluster_perm/',
            views.release_add_cluster_perm,
            name='release_add_cluster_perm'),



        # url(r'^cluster_list_secured/$',
        #     views.get, name='cluster_list_secured'),
        # url(r'^dashboard/$',
        #     views.dashboard, name='dashboard'),
        # url(r'^home/$',
        #     views.test_user_role, name='home'),

    ]

urlpatterns = urls + static(settings.MEDIA_URL,
                            document_root=settings.MEDIA_ROOT)
