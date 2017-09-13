from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from .dashboard import urls as dashboard_urls
from .system import urls as system_urls

urls = [
    url(r'^dashboard/', include(dashboard_urls.urlpatterns,
                                namespace='dashboard')),
    url(r'^system/', include(system_urls.urlpatterns,
                             namespace='system')),
]
urlpatterns = urls + static(settings.MEDIA_URL,
                            document_root=settings.MEDIA_ROOT)
