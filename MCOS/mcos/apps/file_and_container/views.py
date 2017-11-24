from __future__ import absolute_import
from django.contrib import messages
# from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from mcos.apps.authentication.auth_plugins.decorators import login_required
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient
from mcos.apps.admin.system.models import SystemCluster
from mcos_resolver_and_ring_server import tasks


# from mcos.apps.lookup_driver import user_ring

# from ...lookup import utils as lookup_utils
# from .. import utils as dashboard_utils


# @login_required(login_url='/auth/login/')
# @permission_required('authentication.admin_role', raise_exception=True)

def get_user_container_list(user_name):
    get_container_list_task = tasks.api_get_container_list.apply_async(
        (user_name,), soft_timeout=10, timeout=10)
    container_list = get_container_list_task.get(timeout=10)
    return container_list
    # get_ref_cluster_tasks = tasks.get_container_ref_clusters.apply_async(
    #     (user_name,), soft_timeout=5, timeout=5)
    # container_ref_clusters = get_ref_cluster_tasks.get(timeout=5)
    # container_list = None
    # for cluster_id in container_ref_clusters:
    #     cluster_info = SystemCluster.objects.filter(id=cluster_id).first()
    #     cluster_status = cluster_info.status
    #     # print (cluster_status)
    #     # print (cluster_info.name)
    #     if cluster_status == SystemCluster.ACTIVE:
    #         cluster_name = cluster_info.name
    #         try:
    #             get_container_list_task = tasks.get_container_list.apply_async(
    #                 (user_name,),
    #                 routing_key=cluster_name + '.get_container_list'
    #             )
    #             container_list = get_container_list_task.get(timeout=5)
    #             if container_list is not None:
    #                 break
    #                 # print(container_list)
    #         except Exception as e:
    #             print ('Failed to retrieval container list from cluster ' + cluster_name)
    # return container_list


@login_required(role='user')
def get_container_list(request):
    try:
        user_access_info = KeyStoneClient.get_request_user_data(request)
        user_name = user_access_info['user']['name']
        container_list = get_user_container_list(user_name)
        if container_list is not None:
            return JsonResponse(
                {'result': 'success', 'container_list': container_list})
        else:
            return JsonResponse({
                'result': 'failed',
                'message': 'failed to connect to container list db'
            })
    except Exception as e:
        print(e)
        return JsonResponse(
            {'result': 'failed',
             'message': 'resolver service error'})


@login_required(role='user')
def get_container_info(request):
    try:
        container_name = request.GET['container_name']
        user_access_info = KeyStoneClient.get_request_user_data(request)
        user_name = user_access_info['user']['name']
        get_container_info_task = \
            tasks.get_container_info.apply_async(
                (user_name, container_name), timeout=30)
        container_info_result = get_container_info_task.get(timeout=30)
        if container_info_result['result'] == 'success':
            # container_info_result['container_info']['size'] = 0.8
            return JsonResponse(
                {'result': 'success',
                 'container_info': container_info_result['container_info']})
        else:
            return JsonResponse(
                {'result': 'failed',
                 'message': container_info_result['message']})

    except Exception as e:
        print(e)
        return JsonResponse({'result': 'failed', 'message': 'Server Error'})


@login_required(role='user')
def create_container(request):
    if request.method == "POST":
        try:
            input_container_name = request.POST['container_name']
            user_access_info = KeyStoneClient.get_request_user_data(request)
            user_name = user_access_info['user']['name']
            # check if container name is exist in container list
            user_container_list = get_user_container_list(user_name)
            is_exist = False
            for container_name in user_container_list:
                if input_container_name == container_name:
                    is_exist = True
            if is_exist:
                return JsonResponse(
                    {'result': 'failed', 'message': input_container_name + ' is exist!'})
            else:
                create_container_task = tasks.api_create_container.apply_async(
                    (user_name, input_container_name), timeout=20
                )
                create_result = create_container_task.get()
                if create_result['is_created'] is True:
                    return JsonResponse({'result': 'success'})
                else:
                    return JsonResponse({'result': 'failed',
                                         'message': create_result['message']})
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed',
                                 'message': 'Server Error.'})


            # @login_required(role='user')
            # def get_role_list(request):
            #     user_access_info = KeyStoneClient.get_request_user_data(request)
            #     user_name = user_access_info['user']['name']
            #     user_role_list = user_access_info.role_names
            #     return user_role_list


            # @login_required(role='user')
            # def get_option_list(request):
            #     user_access_info = KeyStoneClient.get_request_user_data(request)
            #     user_name = user_access_info['user']['name']
            #     user_role_list = user_access_info.role_names
            #     has_admin_role = False
            #     for role in user_role_list:
            #         if role=='admin':
            #             has_admin_role=True
            #     if has_admin_role:
            #         container_list = get_user_container_list(user_name)


@login_required(role='user')
def upload_file(request):
    if request.method == "POST":
        try:
            user_access_info = KeyStoneClient.get_request_user_data(request)
            user_name = user_access_info['user']['name']
            container_name = request.POST['container_name']
            file_name = request.POST['file_name']
            option_name = request.POST['option_name']
            file_data = request.FILES['file_data'].read()
            # check if container name is exist in container list
            # user_container_list = get_user_container_list(user_name)
            # is_exist = False
            # for container_name in user_container_list:
            #     if input_container_name == container_name:
            #         is_exist = True
            # if is_exist:
            #     return JsonResponse(
            #         {'result': 'failed', 'message': input_container_name + ' is exist!'})
            # else:
            #     create_container_task = tasks.api_create_container.apply_async(
            #         (user_name, input_container_name), timeout=20
            #     )
            #     create_result = create_container_task.get()
            #     if create_result['is_created'] is True:
            #         return JsonResponse({'result': 'success'})
            #     else:
            return JsonResponse({'result': 'failed',
                                 'message': create_result['message']})
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed',
                                 'message': 'Server Error.'})
