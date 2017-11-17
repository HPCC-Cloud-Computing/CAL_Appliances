from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from .dashboard import urls as dashboard_urls
from .system import urls as system_urls
from .ring_and_option import urls as ring_and_option_urls

import views

urls = [
    url(r'^$', views.index, name='index'),
    url(r'^dashboard/', include(dashboard_urls.urlpatterns,
                                namespace='dashboard')),
    url(r'^system/', include(system_urls.urlpatterns,
                             namespace='system')),
    url(r'^ring-and-option/', include(ring_and_option_urls.urlpatterns,
                                      namespace='ring_and_option')),
]
urlpatterns = urls


# urlpatterns = urls + static(settings.MEDIA_URL,
#                             document_root=settings.MEDIA_ROOT)
