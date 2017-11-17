from __future__ import absolute_import
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from mcos.apps.authentication.auth_plugins.decorators import \
    login_required
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient
from mcos.apps.lookup_driver import user_ring

# from ...lookup import utils as lookup_utils
# from .. import utils as dashboard_utils


# @login_required(login_url='/auth/login/')
# @permission_required('authentication.admin_role', raise_exception=True)
def index(request):
    return render(request, 'user/index.html', {})


@login_required(role='user')
def dashboard(request):
    return render(request, 'user/dashboard/account_overview.html', {})


@login_required(role='user')
def data_management(request):
    return render(request, 'user/dashboard/data_management.html', {})


@login_required(role='user')
def get_container_list(request):
    try:
        user_access_info = KeyStoneClient.get_request_user_data(request)
        user_id = user_access_info['user']['id']
        user_container_list = user_ring.get_containers(user_id)
        return JsonResponse(
            {'result': 'success', 'container_list': user_container_list})
    except Exception as e:
        print(e)
        return JsonResponse({'result': 'failed'})

# def index(request):
#     return render(request, 'admin/index.html', {})
#
#
# # @login_required(login_url='/auth/login/')
# # @permission_required('authentication.user_role', raise_exception=True)
# def test_user_role(request):
#     return render(request, 'admin_dashboard/home.html', {})
