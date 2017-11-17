from __future__ import absolute_import
import django
import os
import json
import requests
import time
import uuid
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME
from ..system.models import SystemCluster
from mcos.apps.authentication.auth_plugins.decorators import login_required
from mcos.apps.utils.zk_client import LockManager
from mcos.apps.utils.cache import MemcacheClient
from .ring import HashRing, RingCluster

from mcos_resolver_and_ring_server import tasks


def create_core_ring(request, name, ring_type, version, full_name,
                     description):
    memcache_client = MemcacheClient()
    # check if account ring was exist before create ring
    ring_exist = tasks.check_ring_exist.apply_async((name,))
    is_exist = ring_exist.get()
    if is_exist is False:
        # acquire lock from Zookeeper before enter create ring process
        ring_name = name
        ring_version = version
        lock_manager = LockManager()
        is_acquired = \
            lock_manager.acquire_ring_lock(ring_name + '_' + ring_version)
        if is_acquired is True:
            try:
                total_clusters = int(request.POST['totalClusters'])
                cluster_ids = []
                for i in range(0, total_clusters):
                    cluster_ids.append(
                        request.POST['clusters[' + str(i) + ']'])
            except KeyError:
                return False
            ring_clusters = []
            for id in cluster_ids:
                cluster_data = SystemCluster.objects.filter(id=id).first()
                ring_clusters.append(
                    RingCluster(cluster_data.id, cluster_data.name,
                                cluster_data.address_ip,
                                cluster_data.address_port, 100))
            # create account ring with id and version is 1
            new_ring = HashRing(
                id=str(uuid.uuid4()), name=ring_name, full_name=full_name,
                description=description, ring_type=ring_type, version=1,
                ring_clusters=ring_clusters, replica_factor=3
            )
            new_ring.assign_ref_cluster_to_part()
            new_ring_dict = new_ring.to_dict()
            new_ring_json = json.dumps(new_ring_dict)

            cluster_id = memcache_client.get('current_cluster_id')
            # add ring info to shared database and memcached.
            # Use RPC to call to celery server.
            add_ring_task = \
                tasks.add_ring_info.apply_async(
                    (new_ring_json, cluster_id))
            add_ring_result = add_ring_task.get()
            # if add_ring_result == True:
            #     pass
            # else:
            #     pass
            return True
        else:
            return False
    else:
        return False


@login_required(role='admin')
def add_core_ring(request):
    if request.method == "POST":
        ring_type = request.POST['ring_type']
        if ring_type == 'account':
            create_ring_result = create_core_ring(
                request, 'account', 'account', '1', 'Account Ring',
                'Account Ring'
            )
        elif ring_type == 'container':
            create_ring_result = create_core_ring(
                request, 'container', 'container', '1', 'Container Ring',
                'Container Ring'
            )
        elif ring_type == 'group_resolver':
            create_ring_result = create_core_ring(
                request, 'group_resolver', 'group_resolver', '1',
                'Group Resolver Ring','Group Resolver Ring'
            )

        if create_ring_result ==True:
            return JsonResponse({'create_result': 'true',
                                 'message':
                                     'Core Ring is created!'},
                                status=200)
        else:
            return JsonResponse({'create_result': 'false',
                                 'message':
                                     'Create core ring failed.'
                                     ' Try again later.'},
                                status=200)

# currently only support add a new account ring,
# not support multi account ring create/update
@login_required(role='admin')
def add_account_ring(request):
    if request.method == "POST":
        memcache_client = MemcacheClient()
        # check if account ring was exist before create ring
        account_ring_exist = tasks.check_ring_exist.apply_async(('account',))
        is_exist = account_ring_exist.get()
        if is_exist is False:
            # acquire lock from Zookeeper before enter create ring process
            ring_name = 'account'
            ring_version = '1'
            lock_manager = LockManager()
            is_acquired = \
                lock_manager.acquire_ring_lock(ring_name + '_' + ring_version)
            if is_acquired is True:
                try:
                    total_clusters = int(request.POST['totalClusters'])
                    account_cluster_ids = []
                    for i in range(0, total_clusters):
                        account_cluster_ids.append(
                            request.POST['clusters[' + str(i) + ']'])
                except KeyError:
                    return JsonResponse(
                        {'error': 'input data is invalid or missing. '
                                  'Check data again.'}, status=400)
                account_clusters = []
                for id in account_cluster_ids:
                    cluster_data = SystemCluster.objects.filter(id=id).first()
                    account_clusters.append(
                        RingCluster(cluster_data.id, cluster_data.name,
                                    cluster_data.address_ip,
                                    cluster_data.address_port, 100))
                # create account ring with id and version is 1
                account_ring = HashRing(str(uuid.uuid4()), 'account', 1,
                                        account_clusters)
                account_ring.assign_ref_cluster_to_part()
                account_ring_dict = account_ring.to_dict()
                account_ring_json_string = json.dumps(account_ring_dict)

                cluster_id = memcache_client.get('current_cluster_id')
                # add ring info to shared database and memcached.
                # Use RPC to call to celery server.
                add_ring_task = \
                    tasks.add_ring_info.apply_async(
                        (account_ring_json_string, cluster_id))
                add_ring_result = add_ring_task.get()
                if add_ring_result == True:
                    pass
                else:
                    pass
                return JsonResponse({'create_result': 'true',
                                     'message':
                                         'Account Ring is created!'},
                                    status=200)
            else:
                return JsonResponse({'create_result': 'false',
                                     'message':
                                         'Create and update account ring lock '
                                         'is set. Try again later.'},
                                    status=200)

        else:
            return JsonResponse({'create_result': 'false',
                                 'message':
                                     'Ring is exist! Create Ring Failed!'},
                                status=200)


@login_required(role='admin')
def add_container_ring(request):
    if request.method == "POST":
        memcache_client = MemcacheClient()
        # check if account ring was exist before create ring
        container_ring_exist = tasks.check_ring_exist.apply_async(
            ('container',))
        is_exist = container_ring_exist.get()
        if is_exist is False:
            # acquire lock from Zookeeper before enter create ring process
            ring_name = 'container'
            ring_version = '1'
            lock_manager = LockManager()
            is_acquired = \
                lock_manager.acquire_ring_lock(ring_name + '_' + ring_version)
            if is_acquired is True:
                try:
                    total_clusters = int(request.POST['totalClusters'])
                    container_cluster_ids = []
                    for i in range(0, total_clusters):
                        container_cluster_ids.append(
                            request.POST['clusters[' + str(i) + ']'])
                except KeyError:
                    return JsonResponse(
                        {'error': 'input data is invalid or missing. '
                                  'Check data again.'}, status=400)
                container_clusters = []
                for id in container_cluster_ids:
                    cluster_data = SystemCluster.objects.filter(id=id).first()
                    container_clusters.append(
                        RingCluster(cluster_data.id, cluster_data.name,
                                    cluster_data.address_ip,
                                    cluster_data.address_port, 100))
                # create account ring with id and version is 1
                container_ring = HashRing(str(uuid.uuid4()), 'container', 1,
                                          container_clusters)
                container_ring.assign_ref_cluster_to_part()
                container_ring_dict = container_ring.to_dict()
                container_ring_json_string = json.dumps(container_ring_dict)

                cluster_id = memcache_client.get('current_cluster_id')
                # add ring info to shared database and memcached.
                # Use RPC to call to celery server.
                add_ring_task = \
                    tasks.add_ring_info.apply_async(
                        (container_ring_json_string, cluster_id))
                add_ring_result = add_ring_task.get()
                if add_ring_result == True:
                    pass
                else:
                    pass
                return JsonResponse({'create_result': 'true',
                                     'message':
                                         'Container Ring is created!'},
                                    status=200)
            else:
                return JsonResponse({'create_result': 'false',
                                     'message':
                                         'Create and update account ring lock '
                                         'is set. Try again later.'},
                                    status=200)

        else:
            return JsonResponse({'create_result': 'false',
                                 'message':
                                     'Ring is exist! Create Ring Failed!'},
                                status=200)


@login_required(role='admin')
def add_group_resolver_ring(request):
    if request.method == "POST":
        memcache_client = MemcacheClient()
        # check if account ring was exist before create ring
        group_resolver_ring_exist = tasks.check_ring_exist.apply_async(
            ('group_resolver',))
        is_exist = group_resolver_ring_exist.get()
        if is_exist is False:
            # acquire lock from Zookeeper before enter create ring process
            ring_name = 'group_resolver'
            ring_version = '1'
            lock_manager = LockManager()
            is_acquired = \
                lock_manager.acquire_ring_lock(ring_name + '_' + ring_version)
            if is_acquired is True:
                try:
                    total_clusters = int(request.POST['totalClusters'])
                    group_resolver_cluster_ids = []
                    for i in range(0, total_clusters):
                        group_resolver_cluster_ids.append(
                            request.POST['clusters[' + str(i) + ']'])
                except KeyError:
                    return JsonResponse(
                        {'error': 'input data is invalid or missing. '
                                  'Check data again.'}, status=400)
                group_resolver_clusters = []
                for id in group_resolver_cluster_ids:
                    cluster_data = SystemCluster.objects.filter(id=id).first()
                    group_resolver_clusters.append(
                        RingCluster(cluster_data.id, cluster_data.name,
                                    cluster_data.address_ip,
                                    cluster_data.address_port, 100))
                # create account ring with id and version is 1
                group_resolver_ring = HashRing(str(uuid.uuid4()),
                                               'group_resolver',
                                               1, group_resolver_clusters)
                group_resolver_ring.assign_ref_cluster_to_part()
                group_resolver_ring_dict = group_resolver_ring.to_dict()
                group_resolver_ring_json_string = \
                    json.dumps(group_resolver_ring_dict)

                cluster_id = memcache_client.get('current_cluster_id')
                # add ring info to shared database and memcached.
                # Use RPC to call to celery server.
                add_ring_task = \
                    tasks.add_ring_info.apply_async(
                        (group_resolver_ring_json_string, cluster_id))
                add_ring_result = add_ring_task.get()
                if add_ring_result == True:
                    pass
                else:
                    pass
                return JsonResponse({'create_result': 'true',
                                     'message':
                                         'Group Resolver Ring is created!'},
                                    status=200)
            else:
                return JsonResponse({'create_result': 'false',
                                     'message':
                                         'Create and update group resolver ring lock '
                                         'is set. Try again later.'},
                                    status=200)

        else:
            return JsonResponse({'create_result': 'false',
                                 'message':
                                     'Ring is exist! Create Ring Failed!'},
                                status=200)


@login_required(role='admin')
def update_account_ring(request):
    pass
