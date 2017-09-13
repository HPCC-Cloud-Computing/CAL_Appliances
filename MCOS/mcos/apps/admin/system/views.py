from __future__ import absolute_import
import django
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import SystemNode
from .forms import ConnectToSystemForm, NewNodeDataForm


# from ...lookup import utils as lookup_utils
# from .. import utils as dashboard_utils


class SendNewNodeInfoError(Exception):
    pass


def node_list_info(request):
    if request.method == 'GET':
        node_list_info_dict = {
            'node_list': []
        }
        node_list = SystemNode.objects.all()
        for node_info in node_list:
            node_info_dict = {
                'name': node_info.name,
                'status': node_info.status,
                'service_info': {
                    'service_type': node_info.service_info.service_type,
                    'specifications': node_info.service_info.specifications,
                    'access_info': node_info.service_info.access_info,
                    'distance_info': node_info.service_info.distance_info
                }
            }
            node_list_info_dict['node_list'].append(node_info_dict)
        return HttpResponse(json.dumps(node_list_info_dict),
                            content_type="application/json")


# def send_new_node_info(destination_node, new_node_name, new_node_address):
#     pass

@ensure_csrf_cookie
def connect_to_system(request):
    if request.method == "GET":
        return JsonResponse({'accept_connect': 'true'})
    if request.method == "POST":
        system_form = ConnectToSystemForm(request.POST)
        if system_form.is_valid():
            # check connection to another node in system
            # if all connection is alive, accept node
            new_node_name = system_form.cleaned_data['node_name']
            new_node_address = system_form.cleaned_data['node_address']
            # send new node information to another node
            # return to new node
            node_list = SystemNode.objects.all()
            try:
                for node in node_list:
                    send_new_node_info(node, new_node_name, new_node_address)
            except SendNewNodeInfoError:
                pass
            # if no error has occur, add new_node to node list
            new_node = SystemNode(name=new_node_name, address=new_node_address)
            new_node.save()

            return JsonResponse({'is_connected_to_system': 'true'})
        else:
            return JsonResponse({'error': 'invalid node data format.'})


def check_health(request):
    if request.method == 'GET':
        return JsonResponse({'current_status': 'active'})


def join_new_node(request):
    if request.method == "GET":
        return JsonResponse({'accept_connect': 'true'})

    if request.method == "POST":
        system_form = ConnectToSystemForm(request.POST)
        if system_form.is_valid():
            # check connection to another node in system
            # if all connection is alive, accept node
            new_node_name = system_form.cleaned_data['node_name']
            new_node_address = system_form.cleaned_data['node_address']
            new_node = SystemNode(name=new_node_name, address=new_node_address)
            new_node.save()

            return JsonResponse({'new_node_joined': 'true'})
        else:
            return JsonResponse({'error': 'invalid node data format.'})


@ensure_csrf_cookie
def test_add_new_node(request):
    if request.method == "GET":
        return JsonResponse({'accept_connect': 'true'})

    if request.method == "POST":
        system_form = NewNodeDataForm(request.POST)
        if system_form.is_valid():
            # check connection to another node in system
            # if all connection is alive, accept node
            new_node_name = system_form.cleaned_data['node_name']
            new_node_address = system_form.cleaned_data['node_address']
            new_node = SystemNode(name=new_node_name, address=new_node_address)
            new_node.save()

            return JsonResponse({'new_node_joined': 'true'})
        else:
            return JsonResponse({'error': 'invalid or duplicated node data.'})

# @login_required(login_url='/auth/login/')
# @permission_required('authentication.user_role', raise_exception=True)
# def test_user_role(request):
#     return render(request, 'admin_dashboard/home.html', {})
