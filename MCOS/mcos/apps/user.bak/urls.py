# from django.conf.urls import url
# from django.views.generic import TemplateView
# from django.conf.urls.static import static
# from django.conf import settings
#
# from .views import clouds, files, home, user
#
# urls = \
#     [
#         url(r'^$',
#             home.index, name='index'),
#         url(r'^adminlte/$',
#             home.adminlte, name='adminlte'),
#         url(r'^home/$',
#             home.show_home, name='home'),
#         url(r'^clouds/$',
#             clouds.list_clouds, name='clouds'),
#         url(r'^clouds/update_cloud/',
#             clouds.update_cloud, name='update_cloud'),
#         url(r'^files/$',
#             files.list_files, name='files'),
#         url(r'^files/(?P<folder_id>\d+)/upload/$',
#             files.upload_file, name='upload_file'),
#         url(r'^files/refresh/$',
#             files.refresh_status, name='refresh_status'),
#         url(r'^files/upload/$',
#             files.upload_file, name='upload_root_file'),
#         url(r'^files/(?P<folder_id>\d+)/create/$',
#             files.create_folder, name='create_folder'),
#         url(r'^files/create/$',
#             files.create_folder, name='create_root_folder'),
#         url(r'^files/delete/$',
#             files.delete_files, name='delete_files'),
#         url(r'^files/download/$',
#             files.download_file, name='download_file'),
#         url(r'^settings/$',
#             TemplateView.as_view(
#                 template_name='user_dashboard/settings.html'),
#             name='settings'),
#         url(r'^user/$',
#             user.update_user, name='user'),
#
#     ]
# urlpatterns = urls + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# pass