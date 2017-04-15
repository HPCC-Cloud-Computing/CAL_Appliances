from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from lookup import views

urlpatterns = [
                  url(r'^init_ring/$', views.init_ring,
                      name='init_ring'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
