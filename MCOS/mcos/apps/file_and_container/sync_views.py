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
import datetime

SERVICE_TYPE = STORAGE_SERVICE_CONFIG['type']
AUTH_INFO = STORAGE_SERVICE_CONFIG['auth_info']


# get container row time stamp
def get_container_time_stamp(request):
    try:
        account_name = request.GET['account_name']
        container_name = request.GET['container_name']
        get_ctn_info_task = tasks.sync_get_container_time_stamp. \
            apply_async((account_name, container_name))
        container_row = get_ctn_info_task.get(timeout=5)
        if container_row is not None:
            return JsonResponse(
                {'result': 'success',
                 'is_exist': 'true',
                 'time_stamp': container_row['time_stamp']
                 })
        else:
            return JsonResponse({
                'result': 'success',
                'is_exist': 'false'

            })
    except Exception as e:
        # print('invalid parameter')
        # print(e)
        return JsonResponse(
            {'result': 'failed',
             'message': 'server error'})


@csrf_exempt
def sync_container_row(request):
    if request.method == "POST":
        container_info = {
            'account_name': request.POST['account_name'],
            'container_name': request.POST['container_name'],
            'date_created': request.POST['date_created'],
            'object_count': request.POST['object_count'],
            'is_deleted': request.POST['is_deleted'],
            'time_stamp': request.POST['time_stamp'],
            'size': request.POST['size']
        }
        tasks.sync_container_row.apply_async((container_info,))
        return JsonResponse({'result': 'success'})


@csrf_exempt
def report_container_row(request):
    if request.method == "POST":
        container_info = {
            'account_name': request.POST['account_name'],
            'container_name': request.POST['container_name'],
            'object_count': request.POST['object_count'],
            'time_stamp': request.POST['time_stamp'],
            'size': request.POST['total_size']
        }
        tasks.process_container_row_report.apply_async((container_info,))
        return JsonResponse({'result': 'success'})


# get container row time stamp
def get_object_info_time_stamp(request):
    try:
        account_name = request.GET['account_name']
        container_name = request.GET['container_name']
        object_name = request.GET['object_name']
        get_obj_info_task = tasks.sync_get_object_time_stamp. \
            apply_async((account_name, container_name, object_name))
        obj_info_row = get_obj_info_task.get(timeout=5)

        if obj_info_row is not None:
            return JsonResponse(
                {'result': 'success',
                 'is_exist': 'true',
                 'time_stamp': obj_info_row['time_stamp']
                 })
        else:
            return JsonResponse({
                'result': 'success',
                'is_exist': 'false'

            })
    except Exception as e:
        # print('invalid parameter')
        # print(e)
        return JsonResponse(
            {'result': 'failed',
             'message': 'server error'})


@csrf_exempt
def sync_object_info_row(request):
    if request.method == "POST":
        object_info = {
            'account_name': request.POST['account_name'],
            'container_name': request.POST['container_name'],
            'object_name': request.POST['object_name'],
            'size': request.POST['size'],
            'last_update': request.POST['last_update'],
            'time_stamp': request.POST['time_stamp'],
            'is_deleted': request.POST['is_deleted']
        }
        tasks.sync_object_row.apply_async((object_info,))
        return JsonResponse({'result': 'success'})


# get container row time stamp
def get_resolver_info_time_stamp(request):
    try:
        account_name = request.GET['account_name']
        container_name = request.GET['container_name']
        object_name = request.GET['object_name']
        get_resolver_info_task = tasks.sync_get_resolver_info_time_stamp. \
            apply_async((account_name, container_name, object_name))
        resolver_info_row = get_resolver_info_task.get(timeout=5)
        if resolver_info_row is not None:
            return JsonResponse(
                {'result': 'success',
                 'is_exist': 'true',
                 'time_stamp': resolver_info_row['time_stamp']
                 })
        else:
            return JsonResponse({
                'result': 'success',
                'is_exist': 'false'

            })
    except Exception as e:
        # print('invalid parameter')
        # print(e)
        return JsonResponse(
            {'result': 'failed',
             'message': 'server error'})


@csrf_exempt
def sync_resolver_info_row(request):
    if request.method == "POST":
        resolver_info = {
            'account_name': request.POST['account_name'],
            'container_name': request.POST['container_name'],
            'object_name': request.POST['object_name'],
            'option_name': request.POST['option_name'],
            'time_stamp': request.POST['time_stamp'],
            'is_deleted': request.POST['is_deleted']
        }
        tasks.sync_resolver_info_row.apply_async((resolver_info,))
        return JsonResponse({'result': 'success'})


def get_object_info(service_connector, obj_storage_name):
    uploaded_object_stat = \
        service_connector.stat_object(STORAGE_CONTAINER_NAME, obj_storage_name)
    object_info = {}
    if SERVICE_TYPE == 'swift':
        object_info = {
            'container_name': uploaded_object_stat['x-object-meta-container.name'],
            'account_name': uploaded_object_stat['x-object-meta-account.name'],
            'object_name': uploaded_object_stat['x-object-meta-object.name'],
            'option_name': uploaded_object_stat['x-object-meta-option.name'],
            'last_update': uploaded_object_stat['x-object-meta-last.update'],
            'time_stamp': uploaded_object_stat['x-object-meta-time.stamp'],
            'is_deleted': uploaded_object_stat['x-object-meta-is.deleted'],
            'file_size': uploaded_object_stat['content-length']  # in byte

        }
    elif SERVICE_TYPE == 'amazon_s3':
        object_info = {
            'container_name': uploaded_object_stat['Metadata']['x-amz-container.name'],
            'account_name': uploaded_object_stat['Metadata']['x-amz-account.name'],
            'object_name': uploaded_object_stat['Metadata']['x-amz-object.name'],
            'option_name': uploaded_object_stat['Metadata']['x-amz-option.name'],
            'last_update': uploaded_object_stat['Metadata']['x-amz-last.update'],
            'time_stamp': uploaded_object_stat['Metadata']['x-amz-time.stamp'],
            'is_deleted': uploaded_object_stat['Metadata']['x-amz-is.deleted'],
            'file_size': uploaded_object_stat['ContentLength']

        }
    return object_info


def get_object_data_time_stamp(request):
    try:
        account_name = request.GET['account_name']
        container_name = request.GET['container_name']
        object_name = request.GET['object_name']

        object_data_exist = True
        object_data_time_stamp = ''
        try:
            service_connector = \
                create_service_connector(SERVICE_TYPE, AUTH_INFO)
            storage_object_name = account_name + '.' + container_name + '.' + object_name
            # object_metadata = service_connector.stat_object(STORAGE_CONTAINER_NAME,
            #                                                 storage_object_name)
            object_metadata = get_object_info(service_connector, storage_object_name)
            object_data_time_stamp = object_metadata['time_stamp']
            # print('time_stamp')
            # print(object_data_time_stamp)
        except Exception as e:
            object_data_exist = False

        if object_data_exist is True:
            return JsonResponse(
                {'result': 'success',
                 'is_exist': 'true',
                 'time_stamp': object_data_time_stamp
                 })
        else:
            return JsonResponse({
                'result': 'success',
                'is_exist': 'false'

            })
    except Exception as e:

        return JsonResponse(
            {'result': 'failed',
             'message': 'server error'})


@csrf_exempt
def sync_object_data(request):
    if request.method == 'POST':
        try:
            account_name = request.POST['account_name']
            container_name = request.POST['container_name']
            object_name = request.POST['object_name']
            last_update = request.POST['last_update']
            option_name = request.POST['option_name']
            object_file_data = request.FILES['file']
            file_size = request.FILES['file'].size
            is_deleted = request.POST['is_deleted']
            time_stamp = request.POST['time_stamp']
        except Exception as e:
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        try:
            service_connector = \
                create_service_connector(SERVICE_TYPE, AUTH_INFO)
            object_exist = True
            obj_storage_name = account_name + '.' + container_name + '.' + object_name
            try:
                object_info = \
                    service_connector.stat_object(STORAGE_CONTAINER_NAME, obj_storage_name)
            except Exception as e:
                print('object not exist!')
                object_exist = False
            if object_exist:
                object_metadata = get_object_info(service_connector, obj_storage_name)
                check_time_stamp = datetime.datetime.strptime(
                    object_metadata['time_stamp'], '%Y-%m-%d %H:%M:%S.%f')
                if (check_time_stamp < datetime.datetime.strptime(
                        time_stamp, '%Y-%m-%d %H:%M:%S.%f')):
                    service_connector.delete_object(STORAGE_CONTAINER_NAME, obj_storage_name)
                else:
                    return JsonResponse({'result': 'failed', 'message': 'not update object'})
            service_connector.upload_object(
                obj=account_name + '.' + container_name + '.' + object_name,
                container=STORAGE_CONTAINER_NAME,
                contents=object_file_data.read(),
                content_length=file_size,
                metadata={'account.name': account_name,
                          'container.name': container_name,
                          'object.name': object_name,
                          'last.update': last_update,
                          'option.name': option_name,
                          'time.stamp': time_stamp,
                          'is.deleted': is_deleted}
            )
            return JsonResponse({'result': 'success', 'message': ''})
        except Exception as e:
            print('catch exception')
            print(e)
            return JsonResponse({'result': 'failed', 'message': str(e)})

            # handle upload data file request and update data file request to storage server
