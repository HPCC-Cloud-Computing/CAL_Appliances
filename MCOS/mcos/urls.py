from django.conf.urls import include, url
# from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# from django.views.generic import TemplateView
from django.conf.urls import (
    handler400, handler403, handler404, handler500
)

urlpatterns = [
                  url(r'^admin/', include('mcos.apps.admin.urls',
                                          namespace='admin')),
                  url(r'^auth/', include('mcos.apps.authentication.urls',
                                         namespace='auth')),
                  # url(r'^', include('mcos.apps.user.urls',
                  #                   namespace='user'))
                  # url(r'^lookup/', include('mcs.apps.lookup.urls',
                  #                          namespace='auth')),

              ] + staticfiles_urlpatterns()

# handler400 = 'django_adminlte_test.views.bad_request'
handler403 = \
    'mcos.apps.handle_exceptions.views.permission_denied'
# handler404 = 'my_app.views.page_not_found'
# handler500 = 'my_app.views.server_error'
