from __future__ import absolute_import
from django.contrib import messages
# from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from mcos.apps.authentication.auth_plugins.decorators import login_required
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient
from mcos_resolver_and_ring_server import tasks


def set_context(request, view_context=None, ):
    user_access_info = KeyStoneClient.get_request_user_data(request)
    user_name = user_access_info['user']['name']
    context = {
        'user_name': user_name
    }
    if view_context is not None:
        context.update(view_context)
    return context


# from mcos.apps.lookup_driver import user_ring

# from ...lookup import utils as lookup_utils
# from .. import utils as dashboard_utils


# @login_required(login_url='/auth/login/')
# @permission_required('authentication.admin_role', raise_exception=True)
def index(request):
    return render(request, 'user/index.html', {})


@login_required(role='user')
def check_role(request):
    token = request.session.get('auth_token')
    admin_client = KeyStoneClient.create_admin_client()
    access_info = admin_client.tokens.validate(token)
    is_admin = False
    for role in access_info.role_names:
        if role == 'admin':
            is_admin = True
    if is_admin:
        return JsonResponse({'role': 'admin'})
    else:
        return JsonResponse({'role': 'user'})


@login_required(role='user')
def dashboard(request):
    return render(request, 'user/dashboard/account_overview.html', set_context(request))


@login_required(role='user')
def data_management(request):
    return render(request, 'user/dashboard/data_management.html', set_context(request))

# @login_required(role='user')
# def get_container_list(request):
#     try:
#         user_access_info = KeyStoneClient.get_request_user_data(request)
#         user_name = user_access_info['user']['name']
#         get_container_info_task = \
#             tasks.get_container_list.apply_async((user_name,))
#         user_container_list = get_container_info_task.get()
#         return JsonResponse(
#             {'result': 'success', 'container_list': user_container_list})
#     except Exception as e:
#         print(e)
#         return JsonResponse({'result': 'failed'})
#
#
# @login_required(role='user')
# def get_container_info(request):
#     try:
#         container_name = request.GET['container_name']
#         user_access_info = KeyStoneClient.get_request_user_data(request)
#         user_name = user_access_info['user']['name']
#         get_container_info_task = \
#             tasks.get_container_info.apply_async(
#                 (user_name, container_name))
#         container_info = get_container_info_task.get()
#         return JsonResponse(
#             {'result': 'success', 'container_info': container_info})
#     except Exception as e:
#         print(e)
#         return JsonResponse({'result': 'failed'})
