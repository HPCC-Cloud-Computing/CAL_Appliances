from __future__ import absolute_import
import os
import requests
import grequests
import datetime
import django
import uuid
import time
from random import shuffle
from django.contrib import messages
# from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from mcos.apps.authentication.auth_plugins.decorators import login_required
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient
from mcos.apps.utils.cache import MemcacheClient
from mcos.apps.admin.system.models import SystemCluster
from mcos_resolver_and_ring_server import tasks


def get_admin_token():
    memcache_client = MemcacheClient()
    admin_token = memcache_client.get_data('admin_token')
    if admin_token is None:
        set_admin_token()
        admin_token = memcache_client.get_data('admin_token')
    return admin_token


def set_admin_token():
    memcache_client = MemcacheClient()
    last_update = memcache_client.get_data('admin_token_last_update')
    # only update token if token is None or if token is set after 30 minutes
    if (last_update is None) or (time.time() - last_update >= 1800):
        admin_token = KeyStoneClient.create_admin_client().session.get_token()
        memcache_client.set_data('admin_token', admin_token)
        memcache_client.set_data('admin_token_last_update', time.time())


def get_csrftoken_from_cluster(cluster_url, http_session):
    get_csrf_token_url = cluster_url + '/file-and-container/csrftoken'
    csrftoken = http_session.get(url=get_csrf_token_url, timeout=3).json()['csrftoken']
    return csrftoken


def test_file_name(request):
    # user_access_info = KeyStoneClient.get_request_user_data(request)
    account_name = request.GET['account_name']
    container_name = request.GET['container_name']
    object_name = request.GET['file_name']
    option_ring_name = 'economy_big'
    get_object_cluster_task = \
        tasks.get_object_cluster_refs.apply_async(
            (account_name, container_name, object_name, option_ring_name))
    object_clusters = get_object_cluster_task.get(timeout=5)
    return JsonResponse({'clusters': object_clusters})


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


# django view
def get_csrf_token(request):
    return JsonResponse(
        {'csrftoken': django.middleware.csrf.get_token(request)})


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
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            container_list_url = cluster_url + '/file-and-container/private/container-details/'
            re_try = 0
            while re_try < 3:
                try:
                    get_ctn_detail_rq = [
                        grequests.get(
                            container_list_url, headers={'X-Auth-Token': mcos_admin_token},
                            params={'account_name': account_name,
                                    'container_name': container_name}, timeout=2
                        )
                    ]
                    grequests.map(get_ctn_detail_rq)
                    get_container_info_resp = get_ctn_detail_rq[0].response
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
                    pass
                    print(e)
                    re_try += 1
                    break
            if connected_to_cluster is True:
                break
        if connected_to_cluster is True:
            return True, container_details, is_exist, ''
        else:
            return False, None, False, 'Failed to connect to Account Clusters in Account Ring'
    else:
        return False, None, False, 'Server Error'


def query_container_object_list(account_name, container_name):
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
                    get_ctn_info_rq = [
                        grequests.get(
                            obj_list_url, headers={'X-Auth-Token': mcos_admin_token},
                            params={'account_name': account_name,
                                    'container_name': container_name}, timeout=2
                        )
                    ]
                    grequests.map(get_ctn_info_rq)
                    get_container_info_resp = get_ctn_info_rq[0].response
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
                    break
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
def send_new_container(account_name, container_name, last_update):
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
                            # 'csrfmiddlewaretoken': csrf_token,
                            'account_name': account_name,
                            'container_name': container_name,
                            'date_created': last_update
                        }, timeout=5)
                    status_code = create_container_resp.status_code
                    if status_code == 200:
                        # connected_to_cluster = True
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

        if response_container_created >= 1:
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
            last_update = str(datetime.datetime.utcnow())
        except Exception as e:
            print(e)
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
                                 'message': 'Container ' + input_container_name + ' is exist!'})
            # create new container
        container_created = send_new_container(
            user_name, input_container_name, last_update)
        if container_created is True:
            return JsonResponse({'result': 'success',
                                 'message': ''})
        else:
            return JsonResponse({'result': 'failed',
                                 'message': ''})


# request which will be sent to account clusters in account ring
# created_object: 0 with update, 1 with upload and -1 with delete
class UpdateContainerInfoRequest:
    def __init__(self, cluster_url, account_name, container_name,
                 last_update, size_changed, object_count_changed):
        self.urls = cluster_url + '/file-and-container/private/update-container-info/'
        self.account_name = account_name
        self.container_name = container_name
        self.last_update = last_update,
        self.size_changed = size_changed
        self.object_count_changed = object_count_changed
        self.request = None
        self.create_request()

    def create_request(self):
        self.request = grequests.post(self.urls,
                                      headers={'X-Auth-Token': get_admin_token()},
                                      data={
                                          'account_name': self.account_name,
                                          'container_name': self.container_name,
                                          'last_update': self.last_update,
                                          'size_changed': self.size_changed,
                                          'object_count_changed': self.object_count_changed
                                      },
                                      timeout=10)


# create requests which will be sent to container clusters in container ring
class UpdateObjectInfoRequest:
    def __init__(self, cluster_url, account_name, container_name,
                 object_name, size, last_update, is_deleted):
        self.urls = cluster_url + '/file-and-container/private/update-object-info/'
        self.account_name = account_name
        self.container_name = container_name
        self.object_name = object_name
        self.size = size
        self.last_update = last_update
        self.is_deleted = is_deleted
        self.request = None
        self.create_request()

    def create_request(self):
        self.request = grequests.post(self.urls,
                                      headers={'X-Auth-Token': get_admin_token()},
                                      data={
                                          'account_name': self.account_name,
                                          'container_name': self.container_name,
                                          'object_name': self.object_name,
                                          'size': self.size,
                                          'last_update': self.last_update,
                                          'is_deleted': self.is_deleted
                                      },
                                      timeout=10)


# create requests which will be sent to resolver clusters in resolver ring
class UpdateResolverInfoRequest:
    def __init__(self, cluster_url, account_name, container_name, object_name,
                 option_name, last_update, is_deleted):
        self.urls = cluster_url + '/file-and-container/private/update-resolver-info/'
        self.account_name = account_name
        self.container_name = container_name
        self.object_name = object_name
        self.option_name = option_name
        self.last_update = last_update
        self.is_deleted = is_deleted
        self.request = None
        self.create_request()

    def create_request(self):
        self.request = grequests.post(self.urls,
                                      headers={'X-Auth-Token': get_admin_token()},
                                      data={
                                          'account_name': self.account_name,
                                          'container_name': self.container_name,
                                          'object_name': self.object_name,
                                          'last_update': self.last_update,
                                          'option_name': self.option_name,
                                          'is_deleted': self.is_deleted
                                      },
                                      timeout=10)


# create requests which will be sent to object cluster to save to storage object server
# use for file upload and file update
class UploadObjectDataRequest:
    def __init__(self, cluster_url, account_name, container_name,
                 object_name, last_update, option_name, temp_file_name):
        self.urls = cluster_url + '/file-and-container/private/upload-object-data/'
        self.account_name = account_name
        self.container_name = container_name
        self.object_name = object_name
        self.last_update = last_update
        self.option_name = option_name
        self.temp_file_name = temp_file_name
        self.request = None
        self.create_request()

    def create_request(self):
        self.request = grequests.post(self.urls,
                                      headers={'X-Auth-Token': get_admin_token()},
                                      data={
                                          'account_name': self.account_name,
                                          'container_name': self.container_name,
                                          'object_name': self.object_name,
                                          'last_update': self.last_update,
                                          'option_name': self.option_name,
                                      },
                                      files={'file': open(self.temp_file_name, 'rb')},
                                      timeout=10)


# create requests which will be sent to object cluster to save to storage object server
# use for file upload and file update
class DeleteObjectDataRequest:
    def __init__(self, cluster_url, account_name, container_name,
                 object_name, last_update):
        self.urls = cluster_url + '/file-and-container/private/delete-object-data/'
        self.account_name = account_name
        self.container_name = container_name
        self.object_name = object_name
        self.last_update = last_update
        self.request = None
        self.create_request()

    def create_request(self):
        self.request = grequests.post(self.urls,
                                      headers={'X-Auth-Token': get_admin_token()},
                                      data={
                                          'account_name': self.account_name,
                                          'container_name': self.container_name,
                                          'object_name': self.object_name,
                                          'last_update': self.last_update,
                                      },
                                      timeout=10)


@login_required(role='user')
def upload_file(request):
    if request.method == "POST":
        user_access_info = KeyStoneClient.get_request_user_data(request)
        account_name = user_access_info['user']['name']
        container_name = request.POST['container_name']
        object_name = request.POST['file_name']
        option_name = request.POST['option_name']
        object_file_data = request.FILES['file_data']
        file_size = request.FILES['file_data'].size
        last_update = str(datetime.datetime.utcnow())
        temp_file_name = str(uuid.uuid4())
        with open(temp_file_name, 'wb+') as temp_file:
            for chunk in object_file_data.chunks():
                temp_file.write(chunk)
        option_ring_name = option_name
        object_info = {
            'object_name': object_name,
            'last_update': last_update,
            'size': file_size,
            'option_name': option_ring_name
        }
        # bugs, we need to save file to django before upload file to storage server
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
                                 'message': 'Container ' + input_container_name + ' is not exist!'})

        obj_list_success, container_object_list, obj_list_msg = \
            query_container_object_list(account_name, container_name)
        if obj_list_success is False:
            return JsonResponse({'result': 'failed',
                                 'message': obj_list_msg})

        object_exist = False
        for check_object in container_object_list:
            if object_name == check_object['object_name']:
                object_exist = True
                break
        if object_exist is True:
            return JsonResponse({'result': 'failed',
                                 'message': 'Object ' + object_name + 'is exist!'})

        get_account_clusters_task = \
            tasks.get_account_clusters_ref.apply_async(
                (account_name,))
        account_clusters = get_account_clusters_task.get(timeout=5)

        get_container_clusters_task = \
            tasks.get_container_clusters_ref.apply_async(
                (account_name, container_name))
        container_clusters = get_container_clusters_task.get(timeout=5)

        get_resolver_clusters_task = \
            tasks.get_resolver_clusters_ref.apply_async(
                (account_name, container_name, object_name))
        resolver_clusters = get_resolver_clusters_task.get(timeout=5)

        get_object_cluster_task = \
            tasks.get_object_cluster_refs.apply_async(
                (account_name, container_name, object_name, option_ring_name))
        object_clusters = get_object_cluster_task.get(timeout=5)

        if account_clusters is None or container_clusters is None or \
                        resolver_clusters is None or object_clusters is None:
            return JsonResponse({'result': 'failed',
                                 'message': 'Failed to get some ring data'})
        # if container is exist and object is not exist, create new data object
        success_container_info = 0
        success_object_info = 0
        success_object_data = 0
        success_resolver_info = 0
        send_container_info_requests = []
        send_resolver_info_requests = []
        send_object_info_requests = []
        send_object_data_requests = []

        for cluster in account_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_container_info_requests.append(
                UpdateContainerInfoRequest(cluster_url, account_name, container_name,
                                           last_update, file_size, object_count_changed=1))
        for cluster in container_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_object_info_requests.append(
                UpdateObjectInfoRequest(cluster_url, account_name, container_name,
                                        object_name, file_size, last_update, False))
        for cluster in resolver_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_resolver_info_requests.append(
                UpdateResolverInfoRequest(cluster_url, account_name, container_name, object_name,
                                          option_name, last_update, False))
        for cluster in object_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_object_data_requests.append(
                UploadObjectDataRequest(cluster_url, account_name, container_name,
                                        object_name, last_update, option_name, temp_file_name))

        remain_requests = []
        for request_info in send_container_info_requests:
            remain_requests.append(request_info.request)
        for request_info in send_object_info_requests:
            remain_requests.append(request_info.request)
        for request_info in send_resolver_info_requests:
            remain_requests.append(request_info.request)
        for request_info in send_object_data_requests:
            remain_requests.append(request_info.request)

        len_ctn_info = len(send_container_info_requests)
        len_obj_info = len(send_object_info_requests)
        len_res_info = len(send_resolver_info_requests)
        len_obj_data = len(send_object_data_requests)
        while len(remain_requests) > 0:
            response_list = grequests.map(remain_requests)
            next_container_info_requests = []
            next_resolver_info_requests = []
            next_object_info_requests = []
            next_object_data_requests = []
            # process send container info response
            for i in range(0, len_ctn_info):
                response = response_list[i]  # i: response index
                request_index = i
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_container_info += 1
                    elif response.status_code == 403:  # admin token expired
                        set_admin_token()
                        send_container_info_requests[request_index].create_request()
                        next_container_info_requests.append(send_container_info_requests[request_index])
            # process send object info response
            for i in range(len_ctn_info,
                           len_ctn_info + len_obj_info):
                request_index = i - len_ctn_info
                response = response_list[i]  # i: response index
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_object_info += 1
                    elif response.status_code == 403:
                        set_admin_token()
                        send_object_info_requests[request_index].create_request()
                        next_object_info_requests.append(send_object_info_requests[request_index])
            # process send resolver info response
            for i in range(len_ctn_info + len_obj_info,
                           len_ctn_info + len_obj_info + len_res_info):
                response = response_list[i]  # i: response index
                request_index = i - (len_ctn_info + len_obj_info)
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_resolver_info += 1
                    elif response.status_code == 403:
                        set_admin_token()
                        send_resolver_info_requests[request_index].create_request()
                        next_resolver_info_requests.append(send_resolver_info_requests[request_index])
            # process send object data response
            for i in range(len_ctn_info + len_obj_info + len_res_info,
                           len_ctn_info + len_obj_info + len_res_info + len_obj_data):
                response = response_list[i]  # i: response index
                request_index = i - (len_ctn_info + len_obj_info + len_res_info)
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_object_data += 1
                    elif response.status_code == 403:
                        set_admin_token()
                        send_object_data_requests[request_index].create_request()
                        next_object_data_requests.append(send_object_data_requests[request_index])

            # next iteration
            send_container_info_requests = next_container_info_requests
            send_resolver_info_requests = next_resolver_info_requests
            send_object_info_requests = next_object_info_requests
            send_object_data_requests = next_object_data_requests

            remain_requests = []
            for request_info in send_container_info_requests:
                remain_requests.append(request_info.request)
            for request_info in send_object_info_requests:
                remain_requests.append(request_info.request)
            for request_info in send_resolver_info_requests:
                remain_requests.append(request_info.request)
            for request_info in send_object_data_requests:
                remain_requests.append(request_info.request)

            len_ctn_info = len(send_container_info_requests)
            len_obj_info = len(send_object_info_requests)
            len_res_info = len(send_resolver_info_requests)
            len_obj_data = len(send_object_data_requests)

        os.remove(temp_file_name)
        if success_object_data >= 1 and success_object_info >= 1 and \
                        success_container_info >= 1 and success_resolver_info >= 1:
            return JsonResponse({'result': 'success', 'message': ''})
        else:
            # handle over failure ( not implement)
            return JsonResponse({'result': 'failed', 'message': 'Some Cluster is unavailable, retry later!'})


# send request to resolver cluster to get object option
def get_object_option(account_name, container_name, object_name):
    option_name = None
    is_exist = False
    connected_to_cluster = False
    get_active_clusters_task = \
        tasks.get_resolver_clusters_ref.apply_async((account_name, container_name, object_name))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        for cluster in active_cluster_refs:
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            container_list_url = cluster_url + '/file-and-container/private/get-object-option/'
            re_try = 0
            while re_try < 3:
                try:
                    get_option_name_resp = session.get(
                        container_list_url, headers={'X-Auth-Token': mcos_admin_token},
                        params={'account_name': account_name,
                                'container_name': container_name,
                                'object_name': object_name}, timeout=3)
                    status_code = get_option_name_resp.status_code
                    if status_code == 200:
                        resp_data = get_option_name_resp.json()
                        if resp_data['result'] == 'success':
                            connected_to_cluster = True
                            print('received data from resolver cluster ' + cluster_url)
                            option_name = resp_data['option_name']
                            is_exist = resp_data['is_exist']
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
            if connected_to_cluster is True:
                break
        if connected_to_cluster is True:
            return True, option_name, is_exist, ''
        else:
            return False, None, False, 'Failed to connect to Resolver Clusters in Resolver Ring'
    else:
        return False, None, False, 'Server Error'


# send request to resolver cluster to get object option
def get_object_info(account_name, container_name, object_name, option_name):
    is_exist = False
    object_info = None
    connected_to_cluster = False
    get_active_clusters_task = tasks.get_object_cluster_refs.apply_async(
        (account_name, container_name, object_name, option_name))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        for cluster in active_cluster_refs:
            mcos_admin_token = get_admin_token()
            session = requests.Session()
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            container_list_url = cluster_url + '/file-and-container/private/get-object-info/'
            re_try = 0
            while re_try < 3:
                try:
                    get_option_name_resp = session.get(
                        container_list_url, headers={'X-Auth-Token': mcos_admin_token},
                        params={'account_name': account_name,
                                'container_name': container_name,
                                'object_name': object_name}, timeout=3)
                    status_code = get_option_name_resp.status_code
                    if status_code == 200:
                        connected_to_cluster = True
                        resp_data = get_option_name_resp.json()
                        if resp_data['result'] == 'success':
                            print('received data from object cluster ' + cluster_url)
                            object_info = resp_data['object_info']
                            is_exist = resp_data['is_exist']
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
            if connected_to_cluster is True:
                break
        if connected_to_cluster is True:
            return True, object_info, is_exist, ''
        else:
            return False, None, False, 'Failed to connect to Object Clusters'
    else:
        return False, None, False, 'Server Error'


@login_required(role='user')
def get_file_info(request):
    if request.method == 'GET':
        try:
            container_name = str(request.GET['container_name'])
            object_name = str(request.GET['file_name'])
            user_access_info = KeyStoneClient.get_request_user_data(request)
            account_name = user_access_info['user']['name']
        except Exception as e:
            print (e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        is_success, option_name, is_exist, msg = \
            get_object_option(account_name, container_name, object_name)
        if is_success is False:
            return JsonResponse({'result': 'failed', 'message': msg}, status=400)
        elif is_exist is False:
            return JsonResponse({'result': 'failed', 'message': 'Object Resolver Info Not Found'},
                                status=400)
        is_success, object_info, is_exist, msg = \
            get_object_info(account_name, container_name, object_name, option_name)
        if is_success is False:
            return JsonResponse({'result': 'failed', 'message': msg}, status=400)
        elif is_exist is False:
            return JsonResponse({'result': 'failed', 'message': 'Object Not Found'},
                                status=400)
        else:
            return JsonResponse({'result': 'success', 'object_info': object_info, 'message': ''}, status=200)


@login_required(role='user')
def download_file(request):
    if request.method == 'GET':
        try:
            container_name = str(request.GET['container_name'])
            object_name = str(request.GET['file_name'])
            user_access_info = KeyStoneClient.get_request_user_data(request)
            account_name = user_access_info['user']['name']
        except Exception as e:
            print (e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        is_success, option_name, is_exist, msg = \
            get_object_option(account_name, container_name, object_name)
        if is_success is False:
            return JsonResponse({'result': 'failed', 'message': msg}, status=404)
        elif is_exist is False:
            return JsonResponse({'result': 'failed', 'message': 'Object Resolver Info Not Found'},
                                status=404)
        else:
            get_active_clusters_task = tasks.get_object_cluster_refs.apply_async(
                (account_name, container_name, object_name, option_name))
            active_cluster_refs = get_active_clusters_task.get(timeout=2)
            shuffle(active_cluster_refs)
            if active_cluster_refs is not None:
                for cluster in active_cluster_refs:
                    mcos_admin_token = get_admin_token()
                    cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
                    internal_download_file_url = \
                        cluster_url + '/file-and-container/private/download-object/'
                    re_try = 0
                    while re_try < 3:
                        try:
                            data_resp = requests.get(
                                internal_download_file_url,
                                headers={'X-Auth-Token': mcos_admin_token},
                                params={'account_name': account_name,
                                        'container_name': container_name,
                                        'object_name': object_name}, timeout=5, stream=True)
                            if data_resp.status_code == 200:
                                # return stream response to client
                                # filename = "ox_wallpaper2.png"
                                # f_stream = open(filename, 'rb')
                                # content = 'any string generated by django'
                                # response = HttpResponse(content, content_type='text/plain')
                                # response = HttpResponse(content)
                                response = StreamingHttpResponse(streaming_content=data_resp)
                                # resp['Content-Disposition'] = 'attachment; filename="123.txt"'
                                response['Content-Disposition'] = \
                                    'attachment; filename={0}'.format(object_name)
                                return response

                            elif data_resp.status_code == 403:  # token expired
                                re_try += 1
                                set_admin_token()
                                mcos_admin_token = get_admin_token()
                            elif data_resp.status_code == 404:
                                return JsonResponse(
                                    {'message': 'Object ' + object_name + ' not found!'},
                                    status=404)
                        except Exception as e:
                            print(e)
                            print ('Failed to connect to Server ' + cluster_url)
                            break
                # if cannot connect to any object cluster, return 404
                return JsonResponse(
                    {'message': 'Failed to retrieval object data. '
                                'Cannot connect to Object Clusters. Retry later!'},
                    status=404)
            else:
                return JsonResponse(
                    {'message': 'Failed to retrieval object data. '
                                'Cannot connect to Object Clusters. Retry later!'},
                    status=404)


def send_delete_container(account_name, container_name):
    response_container_deleted = 0
    get_active_clusters_task = \
        tasks.get_account_clusters_ref.apply_async((account_name,))
    active_cluster_refs = get_active_clusters_task.get(timeout=2)
    shuffle(active_cluster_refs)
    if active_cluster_refs is not None:
        re_try = 0
        mcos_admin_token = get_admin_token()
        while re_try < 3:
            try:
                delete_rq_list = []
                for cluster in active_cluster_refs:
                    cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
                    create_container_url = cluster_url + '/file-and-container/private/delete-container/'
                    delete_ctn_rq = grequests.post(
                        create_container_url,
                        headers={'X-Auth-Token': mcos_admin_token},
                        data={
                            'account_name': account_name,
                            'container_name': container_name,
                            'last_update': str(datetime.datetime.utcnow())
                        }, timeout=5)
                    delete_rq_list.append(delete_ctn_rq)
                grequests.map(delete_rq_list)
                token_expr = False
                for resp in delete_rq_list:
                    if resp.response is not None:
                        resp = resp.response
                        status_code = resp.status_code
                        if status_code == 200:
                            resp_data = resp.json()
                            if resp_data['result'] == 'success':
                                response_container_deleted += 1
                        elif status_code == 403:  # token expired
                            token_expr = True
                            set_admin_token()
                            mcos_admin_token = get_admin_token()
                            break
                if token_expr:
                    re_try += 1
                else:
                    break

            except Exception as e:
                print(e)
                print('Failed to connect to Server ' + cluster_url)
                break
        if response_container_deleted >= 1:
            return True
        else:
            return False
    else:
        return False


@login_required(role='user')
def delete_container(request):
    if request.method == "POST":
        try:
            input_container_name = request.POST['container_name']
            user_access_info = KeyStoneClient.get_request_user_data(request)
            user_name = user_access_info['user']['name']
        except Exception as e:
            print(e)
            return JsonResponse({'result': 'failed', 'message': 'invalid parameter'})
        container_deleted = send_delete_container(
            user_name, input_container_name)
        if container_deleted is True:
            return JsonResponse({'result': 'success',
                                 'message': ''})
        else:
            return JsonResponse({'result': 'failed',
                                 'message': ''})


@login_required(role='user')
def update_file(request):
    if request.method == "POST":
        user_access_info = KeyStoneClient.get_request_user_data(request)
        account_name = user_access_info['user']['name']
        container_name = request.POST['container_name']
        object_name = request.POST['file_name']
        object_file_data = request.FILES['file_data']
        updated_file_size = request.FILES['file_data'].size
        last_update = str(datetime.datetime.utcnow())
        temp_file_name = str(uuid.uuid4())
        with open(temp_file_name, 'wb+') as temp_file:
            for chunk in object_file_data.chunks():
                temp_file.write(chunk)

        object_option = get_object_option(account_name, container_name, object_name)[1]
        current_object_info = get_object_info(account_name, container_name, object_name, object_option)[1]

        # check size change in bytes
        object_change_size = updated_file_size - int(current_object_info['file_size'])

        get_account_clusters_task = \
            tasks.get_account_clusters_ref.apply_async(
                (account_name,))
        account_clusters = get_account_clusters_task.get(timeout=5)

        get_container_clusters_task = \
            tasks.get_container_clusters_ref.apply_async(
                (account_name, container_name))
        container_clusters = get_container_clusters_task.get(timeout=5)

        get_resolver_clusters_task = \
            tasks.get_resolver_clusters_ref.apply_async(
                (account_name, container_name, object_name))
        resolver_clusters = get_resolver_clusters_task.get(timeout=5)

        get_object_cluster_task = \
            tasks.get_object_cluster_refs.apply_async(
                (account_name, container_name, object_name, object_option))
        object_clusters = get_object_cluster_task.get(timeout=5)

        if account_clusters is None or container_clusters is None or \
                        resolver_clusters is None or object_clusters is None:
            return JsonResponse({'result': 'failed',
                                 'message': 'Failed to get some ring data'})

        # update object file, and update container information and account information

        # get current object size to calculate changed byte in container size

        success_container_info = 0
        success_object_info = 0
        success_object_data = 0

        send_container_info_requests = []
        send_object_info_requests = []
        send_object_data_requests = []

        for cluster in account_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_container_info_requests.append(
                UpdateContainerInfoRequest(cluster_url, account_name, container_name,
                                           last_update, object_change_size, object_count_changed=0))

        for cluster in container_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_object_info_requests.append(
                UpdateObjectInfoRequest(cluster_url, account_name, container_name,
                                        object_name, updated_file_size, last_update, False))

        for cluster in object_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_object_data_requests.append(
                UploadObjectDataRequest(cluster_url, account_name, container_name,
                                        object_name, last_update, object_option, temp_file_name))

        remain_requests = []
        for request_info in send_container_info_requests:
            remain_requests.append(request_info.request)

        for request_info in send_object_info_requests:
            remain_requests.append(request_info.request)

        for request_info in send_object_data_requests:
            remain_requests.append(request_info.request)

        len_ctn_info = len(send_container_info_requests)
        len_obj_info = len(send_object_info_requests)
        len_obj_data = len(send_object_data_requests)

        while len(remain_requests) > 0:
            response_list = grequests.map(remain_requests)
            next_container_info_requests = []
            next_object_info_requests = []
            next_object_data_requests = []
            # process send container info response
            for i in range(0, len_ctn_info):
                response = response_list[i]  # i: response index
                request_index = i
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_container_info += 1
                    elif response.status_code == 403:  # admin token expired
                        set_admin_token()
                        send_container_info_requests[request_index].create_request()
                        next_container_info_requests.append(send_container_info_requests[request_index])
            # process send object info response
            for i in range(len_ctn_info,
                           len_ctn_info + len_obj_info):
                request_index = i - len_ctn_info
                response = response_list[i]  # i: response index
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_object_info += 1
                    elif response.status_code == 403:
                        set_admin_token()
                        send_object_info_requests[request_index].create_request()
                        next_object_info_requests.append(send_object_info_requests[request_index])
            # process send object data response
            for i in range(len_ctn_info + len_obj_info,
                           len_ctn_info + len_obj_info + len_obj_data):
                response = response_list[i]  # i: response index
                request_index = i - (len_ctn_info + len_obj_info)
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_object_data += 1
                    elif response.status_code == 403:
                        set_admin_token()
                        send_object_data_requests[request_index].create_request()
                        next_object_data_requests.append(send_object_data_requests[request_index])

            # next iteration
            send_container_info_requests = next_container_info_requests
            send_object_info_requests = next_object_info_requests
            send_object_data_requests = next_object_data_requests

            remain_requests = []
            for request_info in send_container_info_requests:
                remain_requests.append(request_info.request)

            for request_info in send_object_info_requests:
                remain_requests.append(request_info.request)

            for request_info in send_object_data_requests:
                remain_requests.append(request_info.request)

            len_ctn_info = len(send_container_info_requests)
            len_obj_info = len(send_object_info_requests)
            len_obj_data = len(send_object_data_requests)

        os.remove(temp_file_name)
        if success_object_data >= 1 and success_object_info >= 1 and success_container_info >= 1:
            return JsonResponse({'result': 'success', 'message': ''})
        else:
            # handle over failure ( not implement)
            return JsonResponse({'result': 'failed', 'message': 'Some Cluster is unavailable, retry later!'})


@login_required(role='user')
def delete_file(request):
    if request.method == "POST":
        user_access_info = KeyStoneClient.get_request_user_data(request)
        account_name = user_access_info['user']['name']
        object_name = request.POST['object_name']
        container_name = request.POST['container_name']
        last_update = str(datetime.datetime.utcnow())
        object_option_name = get_object_option(account_name, container_name, object_name)[1]
        current_object_info = get_object_info(account_name, container_name,
                                              object_name, object_option_name)[1]
        object_change_size = - int(current_object_info['file_size'])

        get_account_clusters_task = \
            tasks.get_account_clusters_ref.apply_async(
                (account_name,))
        account_clusters = get_account_clusters_task.get(timeout=5)

        get_container_clusters_task = \
            tasks.get_container_clusters_ref.apply_async(
                (account_name, container_name))
        container_clusters = get_container_clusters_task.get(timeout=5)

        get_resolver_clusters_task = \
            tasks.get_resolver_clusters_ref.apply_async(
                (account_name, container_name, object_name))
        resolver_clusters = get_resolver_clusters_task.get(timeout=5)

        get_object_cluster_task = \
            tasks.get_object_cluster_refs.apply_async(
                (account_name, container_name, object_name, object_option_name))
        object_clusters = get_object_cluster_task.get(timeout=5)

        if account_clusters is None or container_clusters is None or \
                        resolver_clusters is None or object_clusters is None:
            return JsonResponse({'result': 'failed',
                                 'message': 'Failed to get some ring data'})
        # if container is exist and object is not exist, create new data object
        success_container_info = 0
        success_object_info = 0
        success_object_data = 0
        success_resolver_info = 0

        send_container_info_requests = []
        send_resolver_info_requests = []
        send_object_info_requests = []
        send_object_data_requests = []

        # change object and size of Container
        for cluster in account_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_container_info_requests.append(
                UpdateContainerInfoRequest(cluster_url, account_name, container_name,
                                           last_update, object_change_size, object_count_changed=-1))
        # delete object info in object table
        for cluster in container_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_object_info_requests.append(
                UpdateObjectInfoRequest(cluster_url, account_name, container_name,
                                        object_name, 0, last_update, True))
        # delete resolver info
        for cluster in resolver_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_resolver_info_requests.append(
                UpdateResolverInfoRequest(cluster_url, account_name, container_name, object_name,
                                          ' ', last_update, True))
        # delete object data
        for cluster in object_clusters:
            cluster_url = 'http://' + cluster['address_ip'] + ":" + cluster['address_port']
            send_object_data_requests.append(
                DeleteObjectDataRequest(cluster_url, account_name, container_name, object_name,
                                        last_update))

        remain_requests = []
        for request_info in send_container_info_requests:
            remain_requests.append(request_info.request)
        for request_info in send_object_info_requests:
            remain_requests.append(request_info.request)
        for request_info in send_resolver_info_requests:
            remain_requests.append(request_info.request)
        for request_info in send_object_data_requests:
            remain_requests.append(request_info.request)

        len_ctn_info = len(send_container_info_requests)
        len_obj_info = len(send_object_info_requests)
        len_res_info = len(send_resolver_info_requests)
        len_obj_data = len(send_object_data_requests)

        while len(remain_requests) > 0:
            response_list = grequests.map(remain_requests)
            next_container_info_requests = []
            next_resolver_info_requests = []
            next_object_info_requests = []
            next_object_data_requests = []
            # process send container info response
            for i in range(0, len_ctn_info):
                response = response_list[i]  # i: response index
                request_index = i
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_container_info += 1
                    elif response.status_code == 403:  # admin token expired
                        set_admin_token()
                        send_container_info_requests[request_index].create_request()
                        next_container_info_requests.append(send_container_info_requests[request_index])
            # process send object info response
            for i in range(len_ctn_info,
                           len_ctn_info + len_obj_info):
                request_index = i - len_ctn_info
                response = response_list[i]  # i: response index
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_object_info += 1
                    elif response.status_code == 403:
                        set_admin_token()
                        send_object_info_requests[request_index].create_request()
                        next_object_info_requests.append(send_object_info_requests[request_index])
            # process send resolver info response
            for i in range(len_ctn_info + len_obj_info,
                           len_ctn_info + len_obj_info + len_res_info):
                response = response_list[i]  # i: response index
                request_index = i - (len_ctn_info + len_obj_info)
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_resolver_info += 1
                    elif response.status_code == 403:
                        set_admin_token()
                        send_resolver_info_requests[request_index].create_request()
                        next_resolver_info_requests.append(send_resolver_info_requests[request_index])
            # process send object data response
            for i in range(len_ctn_info + len_obj_info + len_res_info,
                           len_ctn_info + len_obj_info + len_res_info + len_obj_data):
                response = response_list[i]  # i: response index
                request_index = i - (len_ctn_info + len_obj_info + len_res_info)
                if response is not None:
                    if response.status_code == 200 and response.json()['result'] == 'success':
                        success_object_data += 1
                    elif response.status_code == 403:
                        set_admin_token()
                        send_object_data_requests[request_index].create_request()
                        next_object_data_requests.append(send_object_data_requests[request_index])

            # next iteration
            send_container_info_requests = next_container_info_requests
            send_resolver_info_requests = next_resolver_info_requests
            send_object_info_requests = next_object_info_requests
            send_object_data_requests = next_object_data_requests

            remain_requests = []
            for request_info in send_container_info_requests:
                remain_requests.append(request_info.request)
            for request_info in send_object_info_requests:
                remain_requests.append(request_info.request)
            for request_info in send_resolver_info_requests:
                remain_requests.append(request_info.request)
            for request_info in send_object_data_requests:
                remain_requests.append(request_info.request)

            len_ctn_info = len(send_container_info_requests)
            len_obj_info = len(send_object_info_requests)
            len_res_info = len(send_resolver_info_requests)
            len_obj_data = len(send_object_data_requests)
        print('success_object_data ' +str(success_object_data))
        print('success_object_info ' +str(success_object_info))
        print('success_container_info ' +str(success_container_info))
        print('success_resolver_info ' +str(success_resolver_info))

        if success_object_data >= 1 and success_object_info >= 1 and \
                        success_container_info >= 1 and success_resolver_info >= 1:
            return JsonResponse({'result': 'success', 'message': ''})
        else:
            # handle over failure ( not implement)
            return JsonResponse({'result': 'failed', 'message': 'Some Cluster is unavailable, retry later!'})

            # return JsonResponse({'result': 'failed', 'message': 'Some Cluster is unavailable, retry later!'})


def get_account_overview(request):
    user_access_info = KeyStoneClient.get_request_user_data(request)
    account_name = user_access_info['user']['name']
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
            container_list_url = cluster_url + '/file-and-container/private/container-info-list/'
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
        if container_list is not None:
            total_storage_used = 0.0
            total_container = 0
            total_file = 0
            for container_info in container_list:
                total_container += 1
                total_file += container_info['object_count']
                total_storage_used += container_info['size']
            return JsonResponse({'result': 'success',
                                 'total_storage_used': total_storage_used,
                                 'total_container': total_container,
                                 'total_file': total_file})
    msg = 'Failed to get account clusters'
    return JsonResponse({'result': 'failed',
                         'message': msg})
