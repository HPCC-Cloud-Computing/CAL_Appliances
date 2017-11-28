from __future__ import absolute_import
import requests
import datetime
import django
from random import shuffle
from django.contrib import messages
# from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from mcos.apps.authentication.auth_plugins.decorators import login_required
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient
from mcos.apps.utils.cache import MemcacheClient
from mcos.apps.admin.system.models import SystemCluster
from mcos_resolver_and_ring_server import tasks


def get_csrf_token(request):
    return JsonResponse(
        {'csrftoken': django.middleware.csrf.get_token(request)})


def get_admin_token():
    memcache_client = MemcacheClient()
    admin_token = memcache_client.get_data('admin_token')
    if admin_token is None:
        set_admin_token()
        admin_token = memcache_client.get_data('admin_token')
    return admin_token


def set_admin_token():
    memcache_client = MemcacheClient()
    admin_token = KeyStoneClient.create_admin_client().session.get_token()
    memcache_client.set_data('admin_token', admin_token)


def get_csrftoken_from_cluster(cluster_url, http_session):
    get_csrf_token_url = cluster_url + '/file-and-container/csrftoken'
    csrftoken = http_session.get(url=get_csrf_token_url, timeout=3).json()['csrftoken']
    return csrftoken


def query_container_list(account_name):
    get_active_clusters_task = tasks.get_account_clusters_ref.apply_async((account_name,))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    container_list = None
    msg = ''
    if active_cluster_refs is not None:
        container_list = None
        for cluster in active_cluster_refs:
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            container_list_url = cluster_url + '/file-and-container/private/container-list/'
            # csrftoken = get_csrftoken_from_cluster(cluster_url, session)
            re_try = 0
            while re_try < 3:
                try:
                    get_container_list_resp = session.get(
                        container_list_url, headers={'X-Auth-Token': mcos_admin_token},
                        params={'account_name': account_name}, timeout=5
                    )
                    status_code = get_container_list_resp.status_code
                    if status_code == 200:
                        resp_data = get_container_list_resp.json()
                        if resp_data['result'] == 'success':
                            print('received data from account cluster ' + cluster_url)
                            container_list = resp_data['container_list']
                        break
                    elif status_code == 403:  # token expired
                        re_try += 1
                        set_admin_token()
                        mcos_admin_token = get_admin_token()
                except Exception as e:
                    print(e)
                    print ('Failed to connect to Server ' + cluster_url)
                    break
            session.close()
            if container_list is not None:
                break
    else:
        msg = 'Failed to get account clusters'
    if container_list is None:
        msg = 'Failed to get container list from account clusters in Account Ring'
    return container_list, msg


@login_required(role='user')
def get_container_list(request):
    try:
        user_access_info = KeyStoneClient.get_request_user_data(request)
        user_name = user_access_info['user']['name']
    except Exception as e:
        print(e)
        return JsonResponse({'result': 'failed', 'message': 'invalid user name'})
    container_list, err_msg = query_container_list(user_name)
    if container_list is None:
        return JsonResponse({'result': 'failed', 'container_list': None, 'message': err_msg})
    else:
        return JsonResponse({'result': 'success', 'container_list': container_list, 'message': ''})


def get_container_details(account_name, container_name):
    container_details = None
    is_exist = None
    connected_to_cluster = False
    get_active_clusters_task = \
        tasks.get_account_clusters_ref.apply_async((account_name,))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        for cluster in active_cluster_refs:
            # try to get container details from each cluster in account ring cluster list
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            container_list_url = cluster_url + '/file-and-container/private/container-details/'
            re_try = 0
            while re_try < 3:
                try:
                    get_container_info_resp = session.get(
                        container_list_url, headers={'X-Auth-Token': mcos_admin_token},
                        params={'account_name': account_name,
                                'container_name': container_name}, timeout=2)
                    status_code = get_container_info_resp.status_code
                    if status_code == 200:
                        connected_to_cluster = True
                        resp_data = get_container_info_resp.json()
                        if resp_data['result'] == 'success':
                            print('received data from account cluster ' + cluster_url)
                            container_details = resp_data['container_info']
                            is_exist = resp_data['is_exist']
                        break
                    elif status_code == 403:  # token expired
                        re_try += 1
                        set_admin_token()
                        mcos_admin_token = get_admin_token()
                except Exception as e:
                    print(e)
                    print ('Failed to connect to Server ' + cluster_url)
            session.close()
            if connected_to_cluster is True:
                break
        if connected_to_cluster is True:
            return True, container_details, is_exist, ''
        else:
            return False, None, False, 'Failed to connect to Account Clusters in Account Ring'
    else:
        return False, None, False, 'Server Error'


def query_container_object_list(container_name, account_name):
    connected_to_cluster = None
    object_list = []
    get_active_clusters_task = \
        tasks.get_container_clusters_ref.apply_async((account_name, container_name))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        for cluster in active_cluster_refs:
            # try to get container details from each cluster in container ring cluster list
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            obj_list_url = cluster_url + '/file-and-container/private/container-object-list/'
            re_try = 0
            while re_try < 3:
                try:
                    get_container_info_resp = session.get(
                        obj_list_url, headers={'X-Auth-Token': mcos_admin_token},
                        params={'account_name': account_name,
                                'container_name': container_name}, timeout=2)
                    status_code = get_container_info_resp.status_code
                    if status_code == 200:
                        connected_to_cluster = True
                        resp_data = get_container_info_resp.json()
                        if resp_data['result'] == 'success':
                            print('received data from container cluster ' + cluster_url)
                            object_list = resp_data['object_list']
                        break
                    elif status_code == 403:  # token expired
                        re_try += 1
                        set_admin_token()
                        mcos_admin_token = get_admin_token()
                except Exception as e:
                    print(e)
                    print ('Failed to connect to Server ' + cluster_url)
            session.close()
            if connected_to_cluster is True:
                break
        if connected_to_cluster is True:
            return True, object_list, ''
        else:
            return False, None, 'Failed to connect to Container Clusters in Container Ring'
    else:
        return False, None, 'Server Error'


# container info: container details and object list of this container
@login_required(role='user')
def get_container_info(request):
    try:
        user_access_info = KeyStoneClient.get_request_user_data(request)
        account_name = user_access_info['user']['name']
        container_name = request.GET['container_name']
    except Exception as e:
        print(e)
        return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
    info_success, container_details, info_exist, info_msg = \
        get_container_details(account_name, container_name)
    obj_list_success, container_object_list, obj_list_msg = \
        query_container_object_list(account_name, container_name)
    if info_success is False:
        return JsonResponse({'result': 'failed', 'message': info_msg})
    elif info_exist is False:
        return JsonResponse({'result': 'failed',
                             'message': 'Container' + user_access_info + '.' +
                                        container_name + ' Not Found!'})
    elif obj_list_success is False:
        return JsonResponse({'result': 'failed',
                             'message': obj_list_msg})
    else:
        container_info = container_details
        container_info['object_list'] = container_object_list
        return JsonResponse({'result': 'success', 'container_info': container_info,
                             'message': ''})


# send new container to account cluster refs in account ring
def send_new_container(account_name, container_name):
    response_container_created = 0
    get_active_clusters_task = \
        tasks.get_account_clusters_ref.apply_async((account_name,))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        for cluster in active_cluster_refs:
            # send new container to each account cluster
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            print ('Try to connect to cluster' + cluster_url)
            create_container_url = cluster_url + '/file-and-container/private/create-container/'
            re_try = 0
            while re_try < 3:
                try:
                    csrf_token = get_csrftoken_from_cluster(cluster_url, session)
                    create_container_resp = session.post(
                        create_container_url, headers={'X-Auth-Token': mcos_admin_token},
                        data={
                            'csrfmiddlewaretoken': csrf_token,
                            'account_name': account_name,
                            'container_name': container_name,
                            'object_count': 0,
                            'size': 0,
                            'date_created': str(datetime.datetime.utcnow())
                        }, timeout=3)
                    status_code = create_container_resp.status_code
                    if status_code == 200:
                        connected_to_cluster = True
                        resp_data = create_container_resp.json()
                        if resp_data['result'] == 'success':
                            response_container_created += 1
                        break
                    elif status_code == 403:  # token expired
                        re_try += 1
                        set_admin_token()
                        mcos_admin_token = get_admin_token()
                    else:
                        print('Failed to connect to Server ' + cluster_url)
                        break
                except Exception as e:
                    print(e)
                    print('Failed to connect to Server ' + cluster_url)
                    break
            session.close()

        if response_container_created >= 2:
            return True
        else:
            return False
    else:
        return False


@login_required(role='user')
def create_container(request):
    if request.method == "POST":
        try:
            input_container_name = request.POST['container_name']
            user_access_info = KeyStoneClient.get_request_user_data(request)
            user_name = user_access_info['user']['name']
        except Exception as e:
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        # check if container name is exist in container list
        container_list, err_msg = query_container_list(user_name)
        if container_list is None:
            return JsonResponse({'result': 'failed', 'message': err_msg})
        is_exist = False
        for container_name in container_list:
            if container_name == input_container_name:
                is_exist = True
                break
        if is_exist:
            return JsonResponse({'result': 'failed',
                                 'message': 'Container' + input_container_name + ' is exist!'})
            # create new container
        container_created = send_new_container(
            user_name, input_container_name)
        if container_created is True:
            return JsonResponse({'result': 'success',
                                 'message': ''})
        else:
            return JsonResponse({'result': 'failed',
                                 'message': ''})


def send_object_info(account_name, container_name, object_info):
    response_object_info_created = 0
    get_active_clusters_task = \
        tasks.get_container_clusters_ref.apply_async((account_name, container_name))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        for cluster in active_cluster_refs:
            # send new container to each account cluster
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            print ('Try to connect to cluster' + cluster_url)
            create_container_url = cluster_url + '/file-and-container/private/create-object-info/'
            re_try = 0
            while re_try < 3:
                try:
                    csrf_token = get_csrftoken_from_cluster(cluster_url, session)
                    create_obj_info_resp = session.post(
                        create_container_url, headers={'X-Auth-Token': mcos_admin_token},
                        data={
                            'csrfmiddlewaretoken': csrf_token,
                            'account_name': account_name,
                            'container_name': container_name,
                            'object_name': object_info['object_name'],
                            'last_update': object_info['last_update'],
                            'size': object_info['size'],
                        }, timeout=3)
                    status_code = create_obj_info_resp.status_code
                    if status_code == 200:
                        resp_data = create_container_resp.json()
                        if resp_data['result'] == 'success':
                            response_object_info_created += 1
                        break
                    elif status_code == 403:  # token expired
                        re_try += 1
                        set_admin_token()
                        mcos_admin_token = get_admin_token()
                    else:
                        print('Failed to connect to Server ' + cluster_url)
                        break
                except Exception as e:
                    print(e)
                    print('Failed to connect to Server ' + cluster_url)
                    break
            session.close()

    if response_object_info_created >= 2:
        return True
    else:
        return False


def send_resolver_info(account_name, container_name, object_info):
    response_resolver_info_created = 0
    get_active_clusters_task = \
        tasks.get_resolver_clusters_ref.apply_async((account_name, container_name))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        for cluster in active_cluster_refs:
            # send new container to each account cluster
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            print ('Try to connect to cluster' + cluster_url)
            create_container_url = cluster_url + '/file-and-container/private/create-resolver-info/'
            re_try = 0
            while re_try < 3:
                try:
                    csrf_token = get_csrftoken_from_cluster(cluster_url, session)
                    create_obj_info_resp = session.post(
                        create_container_url, headers={'X-Auth-Token': mcos_admin_token},
                        data={
                            'csrfmiddlewaretoken': csrf_token,
                            'account_name': account_name,
                            'container_name': container_name,
                            'object_name': object_info['object_name'],
                            'option_name': object_info['option_name'],
                            'time_stamp': object_info['last_update'],
                        }, timeout=3)
                    status_code = create_obj_info_resp.status_code
                    if status_code == 200:
                        resp_data = create_container_resp.json()
                        if resp_data['result'] == 'success':
                            response_resolver_info_created += 1
                        break
                    elif status_code == 403:  # token expired
                        re_try += 1
                        set_admin_token()
                        mcos_admin_token = get_admin_token()
                    else:
                        print('Failed to connect to Server ' + cluster_url)
                        break
                except Exception as e:
                    print(e)
                    print('Failed to connect to Server ' + cluster_url)
                    break
            session.close()

    if response_resolver_info_created >= 2:
        return True
    else:
        return False


def upload_object_data(account_name, container_name, object_info, object_data):
    response_data_uploaded = 0
    get_active_clusters_task = \
        tasks.get_object_ring_clusters_ref.apply_async((account_name, container_name))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        for cluster in active_cluster_refs:
            # send new container to each account cluster
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            print ('Try to connect to cluster' + cluster_url)
            create_container_url = cluster_url + '/file-and-container/private/upload-object-data/'
            re_try = 0
            while re_try < 3:
                try:
                    csrf_token = get_csrftoken_from_cluster(cluster_url, session)
                    create_obj_info_resp = session.post(
                        create_container_url, headers={'X-Auth-Token': mcos_admin_token},
                        data={
                            'csrfmiddlewaretoken': csrf_token,
                            'account_name': account_name,
                            'container_name': container_name,
                            'object_name': object_info['object_name'],
                            'option_name': object_info['option_name'],
                            'time_stamp': object_info['last_update'],
                        },
                        files={'file': (object_info['object_name'],
                                        object_data)},
                        timeout=3)
                    status_code = create_obj_info_resp.status_code
                    if status_code == 200:
                        resp_data = create_container_resp.json()
                        if resp_data['result'] == 'success':
                            response_data_uploaded += 1
                        break
                    elif status_code == 403:  # token expired
                        re_try += 1
                        set_admin_token()
                        mcos_admin_token = get_admin_token()
                    else:
                        print('Failed to connect to Server ' + cluster_url)
                        break
                except Exception as e:
                    print(e)
                    print('Failed to connect to Server ' + cluster_url)
                    break
            session.close()

    if response_object_info_created >= 2:
        return True
    else:
        return False


@login_required(role='user')
def upload_file(request):
    if request.method == "POST":
        try:
            user_access_info = KeyStoneClient.get_request_user_data(request)
            account_name = user_access_info['user']['name']
            container_name = request.POST['container_name']
            object_file_name = request.POST['file_name']
            option_name = request.POST['option_name']
            object_file_data = request.FILES['file_data']
            file_size = request.FILES['file_data'].size
            last_update = str(datetime.datetime.utcnow())
            file_size_limit = 2 * 1024 * 1024
            if option_name == 'economy':
                if file_size > file_size_limit:
                    option_ring_name = 'economy_big'
                else:
                    option_ring_name = 'economy_small'
            elif option_name == 'speed':
                if file_size > file_size_limit:
                    option_ring_name = 'optimize_big'
                else:
                    option_ring_name = 'optimize_small'
                pass
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed',
                                 'message': 'Invalid parameter.'})
            # check if container name is exist in container list
        container_list, err_msg = query_container_list(account_name)
        if container_list is None:
            return JsonResponse({'result': 'failed', 'message': err_msg})
        container_exist = False
        for check_container_name in container_list:
            if container_name == check_container_name:
                container_exist = True
                break
        if container_exist is False:
            return JsonResponse({'result': 'failed',
                                 'message': 'Container' + input_container_name + ' is not exist!'})

        obj_list_success, container_object_list, obj_list_msg = \
            query_container_object_list(account_name, container_name)
        if obj_list_success is False:
            return JsonResponse({'result': 'failed',
                                 'message': obj_list_msg})

        object_exist = False
        for object_info in container_object_list:
            if object_file_name == object_info['object_name']:
                object_exist = True
                break
        if object_exist is True:
            return JsonResponse({'result': 'failed',
                                 'message': 'Object' + object_file_name + 'is exist!'})
        object_info_created = send_object_info(
            account_name, container_name, {'object_name': object_file_name,
                                           'size': file_size,
                                           'last_update': last_update})
        resolver_info_created = send_resolver_info(
            account_name, container_name, {'object_name': object_file_name,
                                           'option_name': option_ring_name,
                                           'last_update': last_update})
        if object_info_created is True and resolver_info_created is True:
            upload_data_result = upload_object_data(
                account_name, container_name,
                {'object_name': object_file_name,
                 'option_name': option_ring_name,
                 'last_update': last_update},
                object_file_data
            )

