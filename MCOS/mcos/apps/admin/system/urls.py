from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from . import views

urls = \
    [
        url(r'^node_list_info/$',
            views.node_list_info, name='node_list_info'),
        url(r'^test_add_new_node/$',
            views.test_add_new_node, name='test_add_new_node'),
        # url(r'^dashboard/$',
        #     views.dashboard, name='dashboard'),
        # url(r'^home/$',
        #     views.test_user_role, name='home'),

    ]

urlpatterns = urls + static(settings.MEDIA_URL,
                            document_root=settings.MEDIA_ROOT)
