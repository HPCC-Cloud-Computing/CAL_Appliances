from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^init_ring/$', TemplateView.as_view(template_name='lookup/config.html'),
        name='init_ring'),
]
