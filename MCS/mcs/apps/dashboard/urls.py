from django.conf.urls import url
from django.views.generic import TemplateView

from mcs.apps.dashboard.views import files

urlpatterns = [
    url(r'^home/$',
        TemplateView.as_view(template_name='dashboard/home.html'),
        name='home'),
    url(r'^clouds/$',
        TemplateView.as_view(template_name='dashboard/clouds.html'),
        name='clouds'),
    url(r'^files/$',
        files.list_files,
        name='files'),
    url(r'^files/(?P<folder_id>\d+)/upload/$',
        files.create_folder, name='upload_file'),
    url(r'^files/upload/$',
        files.upload_file, name='upload_root_file'),
    url(r'^files/(?P<folder_id>\d+)/create/$',
        files.create_folder, name='create_folder'),
    url(r'^files/create/$',
        files.create_folder, name='create_root_folder'),
    url(r'^files/delete/$',
        files.delete_files, name='delete_files'),
    url(r'^settings/$',
        TemplateView.as_view(template_name='dashboard/settings.html'),
        name='settings'),
    url(r'^user/$',
        TemplateView.as_view(template_name='dashboard/user.html'),
        name='user'),
]
