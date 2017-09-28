from __future__ import absolute_import
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME
from ..system.models import SystemCluster


# from ...lookup import utils as lookup_utils
# from .. import utils as dashboard_utils

def set_context(view_context=None):
    context = {
        'cluster_name': MCOS_CLUSTER_NAME,
        'user_name': 'Administrator 1'
    }
    if view_context is not None:
        context.update(view_context)
    return context


# @login_required(login_url='/auth/login/')
# @permission_required('authentication.admin_role', raise_exception=True)
def dashboard_overview(request):
    return render(request, 'admin/dashboard/index.html',
                  set_context())


def cluster_management(request):
    return render(request, 'admin/dashboard/cluster_management.html',
                  set_context())


def clusters_tbl_api(request):
    cluster_dict_list = []
    cluster_info_list = SystemCluster.objects.all()
    for cluster_info in cluster_info_list:
        cluster_dict_list.append(cluster_info.to_dict())
    return JsonResponse({'cluster_list': cluster_dict_list})


@login_required(login_url='/auth/login/')
@permission_required('authentication.user_role', raise_exception=True)
def test_user_role(request):
    return render(request, 'admin_dashboard/home.html', {})
