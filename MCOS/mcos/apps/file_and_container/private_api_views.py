from __future__ import absolute_import
from django.contrib import messages
from django.http import HttpResponse
# from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from mcos.apps.authentication.auth_plugins.decorators import api_login_required, login_required
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient
from mcos.apps.admin.system.models import SystemCluster
from mcos_resolver_and_ring_server import tasks
from mcos.utils import create_service_connector
from mcos.settings.storage_service_conf import STORAGE_SERVICE_CONFIG, STORAGE_CONTAINER_NAME
from django.views.decorators.csrf import csrf_exempt

SERVICE_TYPE = STORAGE_SERVICE_CONFIG['type']
AUTH_INFO = STORAGE_SERVICE_CONFIG['auth_info']


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


@api_login_required(role='admin')
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


@api_login_required(role='admin')
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


@csrf_exempt
@login_required(role='admin')
def create_container(request):
    if request.method == 'POST':
        try:
            container_name = request.POST['container_name']
            account_name = request.POST['account_name']
            date_created = request.POST['date_created']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
    create_container_task = tasks.update_container_info.apply_async(
        (account_name, container_name, date_created, 0, 0, False, True))
    create_result = create_container_task.get(timeout=10)
    if create_result is True:
        return JsonResponse({'result': 'success'})
    else:
        return JsonResponse({'result': 'failed'})


@csrf_exempt
@login_required(role='admin')
def delete_container(request):
    if request.method == 'POST':
        try:
            container_name = request.POST['container_name']
            account_name = request.POST['account_name']
            last_update = request.POST['last_update']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
    delete_container_task = tasks.update_container_info.apply_async((
        account_name, container_name, last_update, 0, 0, True, False
    ))
    delete_result = delete_container_task.get(timeout=10)
    if delete_result is True:
        return JsonResponse({'result': 'success'})
    else:
        return JsonResponse({'result': 'failed'})


# method handle request update container row in container table
@csrf_exempt
@api_login_required(role='admin')
def update_container_info(request):
    if request.method == 'POST':
        try:
            container_name = request.POST['container_name']
            account_name = request.POST['account_name']
            last_update = request.POST['last_update']
            size_changed = int(request.POST['size_changed'])  # object site in byte
            object_count_changed = int(request.POST['object_count_changed'])
            # print(object_count_changed)
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        size_changed = size_changed * 1.0 / (1024 * 1024)  # convert new object size to MB
        update_container_info_task = tasks.update_container_info.apply_async((
            account_name, container_name, last_update,
            object_count_changed, size_changed, False, False))
        update_result = update_container_info_task.get(timeout=10)
        if update_result is True:
            return JsonResponse({'result': 'success'})
        else:
            return JsonResponse({'result': 'failed'})


# method handle request update object row in object table
@csrf_exempt
@api_login_required(role='admin')
def update_object_info(request):
    if request.method == 'POST':
        try:
            container_name = request.POST['container_name']
            account_name = request.POST['account_name']
            object_name = request.POST['object_name']
            last_update = request.POST['last_update']
            size = int(request.POST['size'])
            is_deleted = request.POST['is_deleted']
            if is_deleted == 'False':
                is_deleted = False
            else:
                is_deleted = True
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})

        update_object_info_task = tasks.update_object_info.apply_async(
            (account_name, container_name, object_name, last_update, size, is_deleted))
        update_result = update_object_info_task.get(timeout=10)
        if update_result is True:
            return JsonResponse({'result': 'success'})
        else:
            return JsonResponse({'result': 'failed'})


# method handle request which data is size of new object push to a container
@csrf_exempt
@api_login_required(role='admin')
def update_resolver_info(request):
    if request.method == 'POST':
        try:
            container_name = request.POST['container_name']
            account_name = request.POST['account_name']
            object_name = request.POST['object_name']
            last_update = request.POST['last_update']
            option_name = request.POST['option_name']
            is_deleted = request.POST['is_deleted']
            if is_deleted == 'False':
                is_deleted = False
            else:
                is_deleted = True
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        update_resolver_info_task = tasks.update_resolver_info.apply_async(
            (account_name, container_name, object_name, option_name, last_update, is_deleted))
        update_result = update_resolver_info_task.get(timeout=10)
        if update_result is True:
            return JsonResponse({'result': 'success'})
        else:
            return JsonResponse({'result': 'failed'})


# handle upload data file request and update data file request to storage server
@csrf_exempt
@api_login_required(role='admin')
def upload_object_data(request):
    if request.method == 'POST':
        try:
            container_name = request.POST['container_name']
            account_name = request.POST['account_name']
            object_name = request.POST['object_name']
            option_name = request.POST['option_name']
            object_file_data = request.FILES['file']
            file_size = request.FILES['file'].size
            last_update = request.POST['last_update']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        try:
            service_connector = \
                create_service_connector(SERVICE_TYPE, AUTH_INFO)
            # check if object exist
            object_exist = True
            obj_storage_name = account_name + '.' + container_name + '.' + object_name
            try:
                # test_result = client.driver.list_containers()
                object_info = client.stat_object(STORAGE_CONTAINER_NAME, obj_storage_name)
            except Exception as e:
                object_exist = False
            # if object exist, delete it and upload new object to storage server
            if object_exist:
                service_connector.delete_object(STORAGE_CONTAINER_NAME, obj_storage_name)
            # upload object to storage server
            service_connector.upload_object(
                obj=account_name + '.' + container_name + '.' + object_name,
                container=STORAGE_CONTAINER_NAME,
                contents=object_file_data.read(),
                content_length=file_size,
                metadata={'account_name': account_name,
                          'container_name': container_name,
                          'object_name': object_name,
                          'last_update': last_update,
                          'option_name': option_name,
                          'time_stamp': last_update,
                          'is_deleted': 'false'}
            )
            return JsonResponse({'result': 'success', 'message': ''})
        except Exception as e:
            print (e)
            return JsonResponse({'result': 'failed', 'message': str(e)})

            # handle upload data file request and update data file request to storage server


@csrf_exempt
@api_login_required(role='admin')
def delete_object_data(request):
    if request.method == 'POST':
        try:
            container_name = request.POST['container_name']
            account_name = request.POST['account_name']
            object_name = request.POST['object_name']
            last_update = request.POST['last_update']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        service_connector = \
            create_service_connector(SERVICE_TYPE, AUTH_INFO)  # check if object exist
        obj_storage_name = account_name + '.' + container_name + '.' + object_name
        try:
            # test_result = client.driver.list_containers()
            object_info = service_connector.stat_object(STORAGE_CONTAINER_NAME, obj_storage_name)
            new_object_info = {
                'account_name': account_name,
                'container_name': container_name,
                'object_name': object_name,
                'option_name': object_info['x-object-meta-option-name'],
                'last_update': last_update,
                'time_stamp': last_update,
                'is_deleted': 'true'
            }
            service_connector.update_object(
                STORAGE_CONTAINER_NAME, obj_storage_name, new_object_info
            )
            print('deleted!')
            return JsonResponse({'result': 'success', 'message': ''})
        except Exception as e:
            print(e)
            print('File not found!')
            # object_exist = False
            return JsonResponse({'result': 'failed',
                                 'message': 'File not found!'})  # method handle request which data is size of new object push to a container


@api_login_required(role='admin')
def get_resolver_info(request):
    if request.method == 'GET':
        try:
            container_name = request.GET['container_name']
            account_name = request.GET['account_name']
            object_name = request.GET['object_name']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        get_resolver_info_task = tasks.get_resolver_info.apply_async(
            (account_name, container_name, object_name))
        option_name = get_resolver_info_task.get(timeout=3)
        if option_name is None:
            return JsonResponse({'result': 'success', 'is_exist': False, 'option_name': ''})
        else:
            return JsonResponse({'result': 'success', 'is_exist': True, 'option_name': option_name})


@api_login_required(role='admin')
def get_object_info(request):
    if request.method == 'GET':
        try:
            container_name = request.GET['container_name']
            account_name = request.GET['account_name']
            object_name = request.GET['object_name']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        try:
            # upload object to storage server
            service_connector = \
                create_service_connector(SERVICE_TYPE, AUTH_INFO)
            # 'conghm.container.1.test3174.tar.gz'
            # uploaded_object_stat = service_connector.stat_object(
            #     STORAGE_CONTAINER_NAME, 'conghm.container.1.test3174.tar.gz')
            uploaded_object_stat = service_connector.stat_object(
                STORAGE_CONTAINER_NAME, account_name + '.' + container_name + '.' + object_name)
            object_info = {
                'container_name': uploaded_object_stat['x-object-meta-container-name'],
                'account_name': uploaded_object_stat['x-object-meta-account-name'],
                'object_name': uploaded_object_stat['x-object-meta-object-name'],
                'option_name': uploaded_object_stat['x-object-meta-option-name'],
                'last_update': uploaded_object_stat['x-object-meta-last-update'],
                'time_stamp': uploaded_object_stat['x-object-meta-time-stamp'],
                'file_size': uploaded_object_stat['content-length']  # in byte

            }
            return JsonResponse({'result': 'success', 'is_exist': True,
                                 'object_info': object_info, 'message': ''})
        except Exception as e:
            print (e)
            return JsonResponse({'result': 'success', 'is_exist': False,
                                 'object_info': '', 'message': 'Object ' + object_name + ' not found!'})


# @api_login_required(role='admin')
@api_login_required(role='admin')
def download_object(request):
    if request.method == 'GET':
        try:
            container_name = request.GET['container_name']
            account_name = request.GET['account_name']
            object_name = request.GET['object_name']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'},
                                status=404)

        try:
            service_connector = \
                create_service_connector(SERVICE_TYPE, AUTH_INFO)
            uploaded_object_stat = service_connector.stat_object(
                STORAGE_CONTAINER_NAME, account_name + '.' + container_name + '.' + object_name)
            object_deleted = uploaded_object_stat['x-object-meta-is-deleted']

            if object_deleted == 'true':
                return JsonResponse({'message': 'Object ' + object_name + ' not found!'},
                                    status=404)

            object_data = service_connector.download_object(
                STORAGE_CONTAINER_NAME, account_name + '.' + container_name + '.' + object_name)
            # resp['Content-Disposition'] = 'attachment; filename="123.txt"'
            # with open(object_name,'wb') as test_f:
            #     test_f.write(object_data)
            response = HttpResponse(object_data[1], status=200)
            response['Content-Disposition'] = \
                'attachment; filename={0}'.format(object_name)
            return response

        except Exception as e:
            print (e)
            return JsonResponse({'message': 'Object ' + object_name + ' not found!'},
                                status=404)
