from __future__ import absolute_import
import django
import json
import requests
import time
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from mcos.apps.authentication.decorators import api_login_required
from .models import SystemCluster, ObjectServiceInfo
from .forms import ConnectToSystemForm, NewClusterDataForm, \
    GainAddClusterPermissionForm, AddNewClusterForm, ReleaseAddClusterPermForm

from mcos.wsgi import SYSTEM_INFO


class SendNewClusterInfoError(Exception):
    pass


@api_login_required()
@permission_required('authentication.admin_role', raise_exception=True)
def get_cluster_list(request):
    if request.method == 'GET':
        cluster_list = []
        cluster_data_list = SystemCluster.objects.all()
        for cluster_info in cluster_data_list:
            cluster_list.append(cluster_info.to_dict())
        return HttpResponse(json.dumps(cluster_list),
                            content_type="application/json")


def login_cluster(session, cluster_url, user_name, password):
    try:
        login_url = cluster_url + "auth/api_login/"
        session.get(login_url)
        csrftoken = session.cookies['csrftoken']
        login_resp = session.post(login_url,
                                  data={'csrfmiddlewaretoken': csrftoken,
                                        'user_name_email': user_name,
                                        'password': password},
                                  timeout=20)
        # check if login is success or not
        if login_resp.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print e.message
        return False


# function used to send request gain add cluster permission
# to a another clusters in system
def gain_add_cluster_perm_from_cluster(cluster_id, cluster_access_info):
    session = requests.Session()
    cluster_url = "http://" + cluster_access_info['ip'] + ":" + \
                  cluster_access_info["port"] + "/"
    is_login = login_cluster(session, cluster_url, 'admin', 'bkcloud')

    if is_login:
        try:
            gain_add_cluster_perm_url = \
                cluster_url + "admin/system/get_add_cluster_permission/"
            retry_connect = True
            while retry_connect:
                session.get(gain_add_cluster_perm_url)
                csrftoken = session.cookies['csrftoken']
                resp = session.post(
                    gain_add_cluster_perm_url,
                    data={
                        'csrfmiddlewaretoken': csrftoken,
                        'request_cluster_id': SYSTEM_INFO[
                            'current_cluster_id']
                    },
                    timeout=105
                )
                status_code = resp.status_code
                if status_code == 200:
                    resp_data = resp.json()
                    if resp_data['acquired_lock'] == 'accept':
                        return 'accept', 'lock is acquired'
                    elif resp_data['acquired_lock'] == 'reject':
                        return 'reject', 'lock is rejected'
                    elif resp_data['acquired_lock'] == 'wait':
                        time.sleep(5)
                else:
                    return "error", "Fail to check permission " \
                                    "from cluster " + str(cluster_id)
        except Exception as e:
            return "error", "Fail to check permission " \
                            "from cluster " + str(cluster_id) + " - " + \
                   "Reason: " + e.message
    else:
        return "error", "Cannot login to cluster " + str(cluster_id)
    session.close()


# function used to send request gain add cluster permission
# to all another clusters in system
def gain_add_cluster_permissions():
    cluster_list = SystemCluster.objects.all()
    cluster_permission_info_list = []
    for cluster in cluster_list:
        if str(cluster.id) != SYSTEM_INFO['current_cluster_id']:
            cluster_access_info = {
                'ip': cluster.address_ip,
                'port': cluster.address_port
            }
            cluster_perm, message = gain_add_cluster_perm_from_cluster(
                str(cluster.id),
                cluster_access_info
            )
            if cluster_perm == 'accept':
                cluster_permission_info_list.append(
                    {'id': str(cluster.id), 'permission': 'accept',
                     'access_info': cluster_access_info}
                )
            elif cluster_perm == 'reject' or cluster_perm == 'error':
                print message
                cluster_permission_info_list.append(
                    {'id': str(cluster.id), 'permission': 'reject',
                     'access_info': cluster_access_info}
                )

    return cluster_permission_info_list


# API that handle process request of another cluster
# which want to gain add_cluster_permission
@api_login_required()
@permission_required('authentication.admin_role', raise_exception=True)
@ensure_csrf_cookie
def get_add_cluster_permission(request):
    if request.method == "GET":
        return JsonResponse({'message': 'This API Provide csrftoken'},
                            status=200)

    if request.method == "POST":
        req_cluster_form = GainAddClusterPermissionForm(request.POST)
        if req_cluster_form.is_valid():
            req_cluster_id = \
                req_cluster_form.cleaned_data['request_cluster_id']
            if SYSTEM_INFO['cts_lock_cluster_id'] != 'none':
                if SYSTEM_INFO['cts_lock_cluster_id'] < req_cluster_id:
                    return JsonResponse({'acquired_lock': 'wait'})
                else:
                    return JsonResponse({'acquired_lock': 'reject'})
            else:
                SYSTEM_INFO['cts_lock_cluster_id'] = req_cluster_id
                return JsonResponse({'acquired_lock': 'accept'})
        else:
            return JsonResponse({'acquired_lock': 'reject',
                                 'message': 'invalid input data'},
                                status=400)


def release_add_cluster_permissions(cluster_permission_list):
    SYSTEM_INFO['cts_lock_cluster_id'] = 'none'
    for cluster in cluster_permission_list:
        session = requests.Session()
        cluster_url = "http://" + cluster['access_info']['ip'] + ":" + \
                      cluster['access_info']["port"] + "/"
        is_login = login_cluster(session, cluster_url, 'admin', 'bkcloud')
        if is_login:
            try:
                add_new_cluster_url = \
                    cluster_url + "admin/system/release_add_cluster_perm/"
                csrftoken = session.cookies['csrftoken']
                resp = session.post(
                    add_new_cluster_url,
                    data={
                        'csrfmiddlewaretoken':
                            csrftoken,
                        'request_cluster_id':
                            SYSTEM_INFO['current_cluster_id'],
                    })
                if resp.status_code == 200 and \
                        resp.json()['release_lock_result'] == 'success':
                    pass
                else:
                    pass
            except Exception as e:
                print e.message
                pass
        else:
            pass
        session.close()


@api_login_required()
@permission_required('authentication.admin_role', raise_exception=True)
@ensure_csrf_cookie
def release_add_cluster_perm(request):
    if SYSTEM_INFO['cts_lock_cluster_id'] != 'none' and \
                    request.method == "POST":
        release_perm_form = \
            ReleaseAddClusterPermForm(request.POST)
        if release_perm_form.is_valid() and \
            release_perm_form.cleaned_data['request_cluster_id'] == \
                SYSTEM_INFO['cts_lock_cluster_id']:
            SYSTEM_INFO['cts_lock_cluster_id'] = 'none'
            return JsonResponse({'release_lock_result': 'success',
                                 'message': 'Add cluster permission lock'
                                            'is released'})
        else:
            return JsonResponse({'release_lock_result': 'failed',
                                 'message': 'only cluster which hold lock can '
                                            'release lock.'}, status=403)
    else:
        return JsonResponse({'release_lock_result': 'failed',
                             'message': 'only cluster which hold lock can '
                                        'release lock.'}, status=403)


# API that handle request from new cluster which want to join the system.
@api_login_required()
@permission_required('authentication.admin_role', raise_exception=True)
@ensure_csrf_cookie
def remote_connect_to_system(request):
    if SYSTEM_INFO['cts_lock_cluster_id'] != 'none':
        return JsonResponse({'accept_connect': 'false',
                             'reason': 'a other new node is being processed.'
                                       'please try again later'}, status=400)
    if request.method == "GET":
        return JsonResponse({'accept_connect': 'true'})
    if request.method == "POST":
        SYSTEM_INFO['cts_lock_cluster_id'] = \
            SYSTEM_INFO['current_cluster_id']
        system_form = ConnectToSystemForm(request.POST)
        if system_form.is_valid():
            # each value cluster['permission'] in cluster_permission_list ]\
            # must be equal with 'accept' or 'reject'
            cluster_permission_list = gain_add_cluster_permissions()
            all_gain_permission = True
            for cluster in cluster_permission_list:
                if cluster['permission'] == 'reject':
                    all_gain_permission = False
            if all_gain_permission:
                add_new_cluster_to_system(system_form, cluster_permission_list)
                release_add_cluster_permissions(cluster_permission_list)
                # return system node list to request cluster
                cluster_dict_list = []
                cluster_info_list = SystemCluster.objects.all()
                for cluster_info in cluster_info_list:
                    cluster_dict_list.append(cluster_info.to_dict())
                return JsonResponse({'is_connected_to_system': 'true',
                                     'cluster_list': cluster_dict_list})
            else:
                release_add_cluster_permissions(cluster_permission_list)
                # return fail to connect to system
                # and tell request cluster try again later
                return JsonResponse({'is_connected_to_system': 'false'})
        else:
            SYSTEM_INFO['cts_lock_cluster_id'] = 'none'
            return JsonResponse({'is_connected_to_system': 'false',
                                 'error': 'invalid cluster data format.'},
                                status=400)


def send_new_cluster_to_other_cluster(cluster_access_info, system_form):
    session = requests.Session()
    result, message = '', ''
    cluster_url = "http://" + cluster_access_info['ip'] + ":" + \
                  cluster_access_info["port"] + "/"
    is_login = login_cluster(session, cluster_url, 'admin', 'bkcloud')
    if is_login:
        try:
            add_new_cluster_url = \
                cluster_url + "admin/system/add_new_cluster/"
            csrftoken = session.cookies['csrftoken']
            resp = session.post(
                add_new_cluster_url,
                data={
                    'csrfmiddlewaretoken': csrftoken,
                    'request_cluster_id': SYSTEM_INFO['current_cluster_id'],
                    'cluster_id': system_form.cleaned_data['cluster_id'],
                    'cluster_name': system_form.cleaned_data['cluster_name'],
                    'cluster_ip': system_form.cleaned_data['cluster_ip'],
                    'cluster_port': system_form.cleaned_data['cluster_port'],
                    'service_info': system_form.cleaned_data['service_info'],
                },
                timeout=100
            )
            status_code = resp.status_code
            if status_code == 200:
                resp_data = resp.json()
                if resp_data['add_cluster_result'] == 'success':
                    result, message = 'success', 'add new cluster successful'
                elif resp_data['add_cluster_result'] == 'failed':
                    result, message = 'failed', \
                                      'fail to add new cluster to cluster' + \
                                      str(cluster_url) + ". Reason: " + \
                                      resp_data['message']
            else:
                result, message = "failed", "Fail to add new cluster to" \
                                            "cluster " + str(cluster_url) \
                                  + ". Reason: Bad Request (HTTP400)"
        except Exception as e:
            result, message = "failed", "Fail to add  add new cluster " \
                                        "to cluster " + str(cluster_url) + \
                              " - " + "Reason: " + e.message
    else:
        result, message = "failed", "Cannot login to cluster " + \
                          str(cluster_url)
    session.close()
    return result, message


def create_cluster_info_from_form(system_form):
    new_cluster_id = system_form.cleaned_data['cluster_id']
    new_cluster_name = system_form.cleaned_data['cluster_name']
    new_cluster_ip = system_form.cleaned_data['cluster_ip']
    new_cluster_port = system_form.cleaned_data['cluster_port']
    new_cluster_info_dict = json.loads(
        system_form.cleaned_data['service_info'])
    new_cluster_service_info = ObjectServiceInfo.create_service_info_data(
        service_id=new_cluster_info_dict['id'],
        service_type_input=new_cluster_info_dict['type'],
        auth_info_input=new_cluster_info_dict['auth_info'],
        service_specs_input=new_cluster_info_dict['specifications']
    )
    new_cluster = SystemCluster(
        id=new_cluster_id,
        name=new_cluster_name,
        address_ip=new_cluster_ip,
        address_port=new_cluster_port,
        service_info=new_cluster_service_info
    )
    return new_cluster, new_cluster_service_info


def add_new_cluster_to_system(system_form, cluster_permission_list):
    # add new cluster to current cluster database
    new_cluster, new_cluster_service_info = \
        create_cluster_info_from_form(system_form)
    new_cluster_service_info.save()
    new_cluster.save()
    # add new cluster to all other clusters in the system
    for cluster in cluster_permission_list:
        resp_result, msg = send_new_cluster_to_other_cluster(
            cluster['access_info'], system_form)
        if resp_result == 'success':
            pass
        elif resp_result == 'failed':
            print msg
            pass
            # delete new cluster data of clusters which sent success message
            # to current cluster
            raise Exception("Add new cluster to system corrupt at cluster" +
                            cluster_access_info['ip'] + ":" +
                            cluster_access_info["port"])


@api_login_required()
@permission_required('authentication.admin_role', raise_exception=True)
@ensure_csrf_cookie
def add_new_cluster(request):
    if SYSTEM_INFO['cts_lock_cluster_id'] != 'none' \
            and request.method == "POST":
        new_cluster_form = AddNewClusterForm(request.POST)
        if new_cluster_form.is_valid():
            request_cluster_id = new_cluster_form. \
                cleaned_data['request_cluster_id']
            if request_cluster_id == SYSTEM_INFO['cts_lock_cluster_id']:
                new_cluster, new_cluster_service_info = \
                    create_cluster_info_from_form(new_cluster_form)
                new_cluster_service_info.save()
                new_cluster.save()
                return JsonResponse({'add_cluster_result': 'success',
                                     'message': 'add new cluster successful.'})
            else:
                return JsonResponse({'add_cluster_result': 'failed',
                                     'message': 'only cluster which hold lock'
                                                'can add new cluster to this'
                                                'clusters.'})
        else:
            return JsonResponse({'add_cluster_result': 'failed',
                                 'message': 'New cluster info is invalid'})

    else:
        return JsonResponse({'add_cluster_result': 'failed',
                             'message': 'only cluster which hold lock can '
                                        'add new cluster to this clusters.'})


@api_login_required()
@permission_required('authentication.admin_role', raise_exception=True)
def check_health(request):
    if request.method == 'GET':
        return JsonResponse({'current_status': 'active'})
