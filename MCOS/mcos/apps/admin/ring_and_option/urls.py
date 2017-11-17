from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from . import views

urls = \
    [
        url(r'^add-core-ring', views.add_core_ring,
            name='add_core_ring'),
        url(r'^add-defined-option-ring', views.add_defined_option_ring,
            name='add_defined_option_ring'),
    ]

urlpatterns = urls
