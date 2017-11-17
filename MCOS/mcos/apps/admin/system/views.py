from __future__ import absolute_import
import django
import os
import json
import requests
import time
import memcache
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from mcos.apps.authentication.auth_plugins.decorators import api_login_required
from mcos.apps.authentication.auth_plugins.keystone_auth import KeyStoneClient
from mcos.utils import set_lock, release_lock, get_shared_value
from mcos.settings import MEMCACHED_IP, MEMCACHED_PORT
from .models import SystemCluster, ObjectServiceInfo
from .forms import ConnectToSystemForm, NewClusterDataForm, \
    GainAddClusterPermissionForm, AddNewClusterForm, ReleaseAddClusterPermForm

from mcos.wsgi import SYSTEM_INFO


class SendNewClusterInfoError(Exception):
    pass


def request_csrf_token(root_url, http_session):
    req_headers = create_auth_token_header()
    get_csrf_token_url = root_url + \
                         'admin/system/get_csrf_token'
    csrftoken = http_session.get(
        url=get_csrf_token_url, headers=req_headers).json()['csrftoken']
    return csrftoken


def create_cluster_url(cluster_access_info):
    cluster_url = "http://" + cluster_access_info['ip'] + ":" + \
                  cluster_access_info["port"] + "/"
    return cluster_url


def create_auth_token_header():
    mcos_admin_token = \
        KeyStoneClient.create_admin_client().session.get_token()
    req_headers = {'X-Auth-Token': mcos_admin_token}
    return req_headers


@api_login_required(role='admin')
def get_csrf_token(request):
    return JsonResponse(
        {'csrftoken': django.middleware.csrf.get_token(request)})


# @api_login_required(role='admin')
# @ensure_csrf_cookie
# def remote_connect_to_system(request):
#     form_data = request.POST
#     return JsonResponse({'form_is_validate': True})


@api_login_required(role='admin')
def get_cluster_list(request):
    if request.method == 'GET':
        cluster_list = []
        cluster_data_list = SystemCluster.objects.all()
        for cluster_info in cluster_data_list:
            cluster_list.append(cluster_info.to_dict())
        return HttpResponse(json.dumps(cluster_list),
                            content_type="application/json")


# function used to send request gain add cluster permission
# to a another clusters in system
def gain_add_cluster_perm_from_cluster(cluster_setup_pid,
                                       cluster_access_info):
    session = requests.Session()
    cluster_url = create_cluster_url(cluster_access_info)
    gain_add_cluster_perm_url = \
        cluster_url + "admin/system/get_add_cluster_permission/"
    csrftoken = request_csrf_token(cluster_url, session)
    auth_token_header = create_auth_token_header()
    try:
        retry_connect = True
        while retry_connect:
            resp = session.post(
                gain_add_cluster_perm_url,
                headers=auth_token_header,
                data={
                    'csrfmiddlewaretoken': csrftoken,
                    'request_cluster_id':
                        cluster_setup_pid
                },
                timeout=600
            )
            status_code = resp.status_code
            if status_code == 200:
                resp_data = resp.json()
                if resp_data['acquired_lock'] == 'accept':
                    print(
                    "cluster " + gain_add_cluster_perm_url + " accept lock")
                    return 'accept', 'lock is acquired'
                elif resp_data['acquired_lock'] == 'reject':
                    print(
                    "cluster " + gain_add_cluster_perm_url + " reject lock")
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
    session.close()


def gain_add_cluster_permissions(cluster_setup_pid):
    cluster_list = SystemCluster.objects.all()
    cluster_permission_info_list = []
    for cluster in cluster_list:
        if str(cluster.id) != get_shared_value('current_cluster_id'):
            cluster_access_info = {
                'ip': cluster.address_ip,
                'port': cluster.address_port
            }
            cluster_perm, message = gain_add_cluster_perm_from_cluster(
                cluster_setup_pid,
                cluster_access_info
            )
            if cluster_perm == 'accept':
                cluster_permission_info_list.append(
                    {'id': str(cluster.id), 'permission': 'accept',
                     'access_info': cluster_access_info}
                )
            elif cluster_perm == 'reject' or cluster_perm == 'error':
                print(message)
                cluster_permission_info_list.append(
                    {'id': str(cluster.id), 'permission': 'reject',
                     'access_info': cluster_access_info}
                )

    return cluster_permission_info_list


# API that handle process request of another cluster
# which want to gain add_cluster_permission
@api_login_required(role='admin')
@ensure_csrf_cookie
def get_add_cluster_permission(request):
    if request.method == "POST":
        req_cluster_form = GainAddClusterPermissionForm(request.POST)
        if req_cluster_form.is_valid():
            req_cluster_id = \
                req_cluster_form.cleaned_data['request_cluster_id']
            cluster_setup_pid = get_shared_value('cluster_setup_pid')
            if cluster_setup_pid is not None:
                if cluster_setup_pid < req_cluster_id:
                    return JsonResponse({'acquired_lock': 'wait'})
                else:
                    return JsonResponse({'acquired_lock': 'reject'})
            else:
                set_lock('cluster_setup_pid', req_cluster_id)
                return JsonResponse({'acquired_lock': 'accept'})
        else:
            return JsonResponse({'acquired_lock': 'reject',
                                 'message': 'invalid input data'},
                                status=400)


def release_add_cluster_permissions(cluster_permission_list):
    for cluster in cluster_permission_list:
        session = requests.Session()
        cluster_url = create_cluster_url(cluster['access_info'])
        add_new_cluster_url = \
            cluster_url + "admin/system/release_add_cluster_perm/"
        csrftoken = request_csrf_token(cluster_url, session)
        auth_token_header = create_auth_token_header()
        try:
            resp = session.post(
                add_new_cluster_url,
                headers=auth_token_header,
                data={
                    'csrfmiddlewaretoken':
                        csrftoken,
                    'request_cluster_id':
                        get_shared_value('cluster_setup_pid'),
                })
            if resp.status_code == 200 and \
                            resp.json()['release_lock_result'] == 'success':
                pass
            else:
                pass
        except Exception as e:
            print (e.message)
            pass
        session.close()
    release_lock('cluster_setup_pid')


@api_login_required(role='admin')
@ensure_csrf_cookie
def release_add_cluster_perm(request):
    if get_shared_value('cluster_setup_pid') and \
                    request.method == "POST":
        release_perm_form = \
            ReleaseAddClusterPermForm(request.POST)
        if release_perm_form.is_valid() and \
                        release_perm_form.cleaned_data['request_cluster_id'] == \
                        get_shared_value('cluster_setup_pid'):
            release_lock('cluster_setup_pid')
            return JsonResponse({'release_lock_result': 'success',
                                 'message': 'cls setup lock is released.'})
    return JsonResponse({'release_lock_result': 'failed',
                         'message': 'only cluster which hold lock can '
                                    'release lock.'}, status=403)


# API that handle request from new cluster which want to join the system.
@api_login_required(role='admin')
@ensure_csrf_cookie
def remote_connect_to_system(request):
    if get_shared_value('cluster_setup_pid') is not None:
        return JsonResponse({'accept_connect': 'false',
                             'reason': 'a other new node is being processed.'
                                       'please try again later'}, status=400)
    if request.method == "GET":
        return JsonResponse({'accept_connect': 'true'})
    if request.method == "POST":
        cluster_setup_pid = str(os.getpid()) + \
                            get_shared_value('current_cluster_id')
        if set_lock('cluster_setup_pid', cluster_setup_pid):
            system_form = ConnectToSystemForm(request.POST)
            if system_form.is_valid():
                cluster_permission_list = \
                    gain_add_cluster_permissions(cluster_setup_pid)
                all_gain_permission = True
                for cluster in cluster_permission_list:
                    if cluster['permission'] == 'reject':
                        all_gain_permission = False
                if all_gain_permission:
                    add_new_cluster_to_system(system_form,
                                              cluster_permission_list)
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
            release_lock('cluster_setup_pid')
        return JsonResponse({'is_connected_to_system': 'false',
                             'error': 'Another process is setup system or '
                                      'invalid cluster data format.'},
                            status=400)


def send_new_cluster_to_other_cluster(cluster_access_info, system_form):
    session = requests.Session()
    result, message = '', ''
    cluster_url = create_cluster_url(cluster_access_info)
    csrftoken = request_csrf_token(cluster_url, session)
    auth_token_header = create_auth_token_header()
    add_new_cluster_url = \
        cluster_url + "admin/system/add_new_cluster/"
    try:
        resp = session.post(
            add_new_cluster_url,
            headers=auth_token_header,
            data={
                'csrfmiddlewaretoken': csrftoken,
                'request_cluster_id':
                    get_shared_value('cluster_setup_pid'),
                'cluster_id': system_form.cleaned_data['cluster_id'],
                'cluster_name': system_form.cleaned_data['cluster_name'],
                'cluster_ip': system_form.cleaned_data['cluster_ip'],
                'cluster_port': system_form.cleaned_data['cluster_port'],
                'service_info': system_form.cleaned_data['service_info'],
            },
            timeout=600
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
    new_cluster, new_cluster_service_info = \
        create_cluster_info_from_form(system_form)
    new_cluster_service_info.save()
    new_cluster.save()
    for cluster in cluster_permission_list:
        resp_result, msg = send_new_cluster_to_other_cluster(
            cluster['access_info'], system_form)
        if resp_result == 'success':
            pass
        elif resp_result == 'failed':
            print(msg)
            raise Exception("Add new cluster to system corrupt at cluster" +
                            cluster_access_info['ip'] + ":" +
                            cluster_access_info["port"])


@api_login_required(role='admin')
@ensure_csrf_cookie
def add_new_cluster(request):
    if get_shared_value('cluster_setup_pid') is not None \
            and request.method == "POST":
        new_cluster_form = AddNewClusterForm(request.POST)
        if new_cluster_form.is_valid():
            request_cluster_id = new_cluster_form. \
                cleaned_data['request_cluster_id']
            if request_cluster_id == get_shared_value('cluster_setup_pid'):
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


@api_login_required(role='admin')
def check_health(request):
    if request.method == 'GET':
        return JsonResponse({'current_status': 'active'})



@api_login_required(role='admin')
def check_health(request):
    if request.method == 'GET':
        return JsonResponse({'current_status': 'active'})
