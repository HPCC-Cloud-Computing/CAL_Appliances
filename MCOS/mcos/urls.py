from django.conf.urls import include, url
# from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# from django.views.generic import TemplateView

urlpatterns = [
                  url(r'^admin/', include('mcos.apps.admin.urls',
                                          namespace='admin')),
                  url(r'^auth/', include('mcos.apps.authentication.urls',
                                         namespace='auth')),
                  # url(r'^lookup/', include('mcs.apps.lookup.urls',
                  #                          namespace='auth')),
                  # url(r'^', include('mcs.apps.user_dashboard.urls',
                  #                   namespace='user_dashboard'))
              ] + staticfiles_urlpatterns()
