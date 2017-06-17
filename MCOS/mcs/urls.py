from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView

urlpatterns = [
                  url(r'^admin/', admin.site.urls),
                  url(r'^auth/', include('authentication.urls')),
                  url(r'^lookup/', include('lookup.urls')),
                  url(r'^', include('dashboard.urls'))
              ] + staticfiles_urlpatterns()
