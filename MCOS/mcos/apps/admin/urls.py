from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from .dashboard import urls as dashboard_urls
from .system import urls as system_urls
import views

urls = [
    url(r'^$', views.index, name='index'),
    url(r'^dashboard/', include(dashboard_urls.urlpatterns,
                                namespace='dashboard')),
    url(r'^system/', include(system_urls.urlpatterns,
                             namespace='system')),
]
urlpatterns = urls
# urlpatterns = urls + static(settings.MEDIA_URL,
#                             document_root=settings.MEDIA_ROOT)


def my_login_required(function):
    def wrapper(request, *args, **kw):
        user=request.user
        if not (user.id and request.session.get('code_success')):
            return HttpResponseRedirect('/splash/')
        else:
            return function(request, *args, **kw)
    return wrapper