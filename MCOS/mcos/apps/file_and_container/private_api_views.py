from __future__ import absolute_import
from django.contrib import messages
# from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from mcos.apps.authentication.auth_plugins.decorators import api_login_required, login_required
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient
from mcos.apps.admin.system.models import SystemCluster
from mcos_resolver_and_ring_server import tasks


@api_login_required(role='admin')
def get_container_list(request):
    try:
        account_name = request.GET['account_name']
        get_container_list_task = tasks.get_container_list.apply_async((account_name,))
        container_list = get_container_list_task.get(timeout=5)
        if container_list is not None:
            return JsonResponse(
                {'result': 'success', 'container_list': container_list})
        else:
            return JsonResponse({
                'result': 'failed',
                'message': 'Failed to connect to container list db'
            })
    except Exception as e:
        print(e)
        return JsonResponse(
            {'result': 'failed',
             'message': 'server error'})


@login_required(role='admin')
def get_container_details(request):
    try:
        account_name = request.GET['account_name']
        container_name = request.GET['container_name']
        get_container_details_task = tasks.get_container_details.apply_async(
            (account_name, container_name))
        container_info = get_container_details_task.get(timeout=5)
        if container_info is not None:
            return JsonResponse({'result': 'success',
                                 'container_info': container_info,
                                 'is_exist': True})
        else:
            return JsonResponse({'result': 'success',
                                 'container_info': container_info,
                                 'is_exist': False})
    except Exception as e:
        print(e)
        return JsonResponse(
            {'result': 'failed',
             'message': 'server error'})


@login_required(role='admin')
def get_container_object_list(request):
    try:
        account_name = request.GET['account_name']
        container_name = request.GET['container_name']
        get_object_list_task = tasks.get_object_list.apply_async(
            (account_name, container_name))
        object_list = get_object_list_task.get(timeout=5)
        return JsonResponse({'result': 'success',
                             'object_list': object_list})
    except Exception as e:
        print(e)
        return JsonResponse(
            {'result': 'failed',
             'message': 'server error'})


@login_required(role='admin')
def create_container(request):
    if request.method == 'POST':
        try:
            container_name = request.POST['container_name']
            account_name = request.POST['account_name']
            container_size = float(request.POST['size'])
            object_count = int(request.POST['object_count'])
            date_created = request.POST['date_created']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
    create_container_task = tasks.create_new_container.apply_async(
        ({'account_name': account_name,
          'container_name': container_name,
          'object_count': object_count,
          'size': container_size,
          'date_created': date_created},))
    create_result = create_container_task.get(timeout=10)
    if create_result is True:
        return JsonResponse({'result': 'success'})
    else:
        return JsonResponse({'result': 'failed'})
