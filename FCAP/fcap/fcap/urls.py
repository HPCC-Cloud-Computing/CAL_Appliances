from django.conf.urls import include, url

urlpatterns = [
    url(r'^auth/', include('apps.authentication.urls')),
    url(r'^', include('apps.management.urls')),
]
