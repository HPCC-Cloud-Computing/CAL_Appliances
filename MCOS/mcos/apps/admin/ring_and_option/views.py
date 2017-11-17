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
            for cluster in ring_clusters:
                print cluster.part_number
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
                'Group Resolver Ring', 'Group Resolver Ring'
            )

        if create_ring_result == True:
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


@login_required(role='admin')
def update_account_ring(request):
    pass


def get_compatible_clusters(option_name, capacity_limit,
                            read10mb_limit, write10mb_limit,
                            read128k_limit, write128k_limit):
    compatible_clusters = []
    system_clusters = SystemCluster.objects.all()
    for cluster in system_clusters:
        cluster_spec = json.loads(cluster.service_info.specifications)
        cluster.weight = int(cluster_spec['capacity'])
        if option_name == 'optimize_big':
            if float(cluster_spec['capacity']) >= capacity_limit and \
                            float(cluster_spec['10mb-read']) >= read10mb_limit and \
                            float(cluster_spec['10mb-write']) >= write10mb_limit:
                compatible_clusters.append(cluster)
        elif option_name == 'economy_big':
            if float(cluster_spec['capacity']) >= capacity_limit and \
                            float(cluster_spec['10mb-read']) < read10mb_limit and \
                            float(cluster_spec['10mb-write']) < write10mb_limit:
                compatible_clusters.append(cluster)
        elif option_name == 'optimize_small':
            if float(cluster_spec['capacity']) <= capacity_limit and \
                            float(cluster_spec['128k-read']) >= read128k_limit and \
                            float(cluster_spec['128k-write']) >= write128k_limit:
                compatible_clusters.append(cluster)
        elif option_name == 'economy_small':
            if float(cluster_spec['capacity']) <= capacity_limit and \
                            float(cluster_spec['128k-read']) < read128k_limit and \
                            float(cluster_spec['128k-write']) < write128k_limit:
                compatible_clusters.append(cluster)

    return compatible_clusters


def create_defined_option_ring(ring_name, full_name, description, ring_type,
                               version, compatible_clusters, replica_factor):
    memcache_client = MemcacheClient()
    # check if account ring was exist before create ring
    ring_exist = tasks.check_ring_exist.apply_async((ring_name,))
    is_exist = ring_exist.get()
    if is_exist is False:
        # acquire lock from Zookeeper before enter create ring process
        ring_version = version
        is_acquired = True
        lock_manager = LockManager()
        is_acquired = \
            lock_manager.acquire_ring_lock(ring_name + '_' + str(ring_version))
        if is_acquired is True:
            ring_clusters = []
            for cluster in compatible_clusters:
                ring_clusters.append(
                    RingCluster(cluster.id, cluster.name,
                                cluster.address_ip,
                                cluster.address_port, cluster.weight))
            # create account ring with id and version is 1
            new_ring = HashRing(
                id=str(uuid.uuid4()), name=ring_name, full_name=full_name,
                description=description, ring_type=ring_type, version=1,
                ring_clusters=ring_clusters, replica_factor=replica_factor
            )
            new_ring.assign_ref_cluster_to_part()
            new_ring_dict = new_ring.to_dict()
            new_ring_json = json.dumps(new_ring_dict)

            cluster_id = memcache_client.get('current_cluster_id')
            # # add ring info to shared database and memcached.
            # # Use RPC to call to celery server.
            add_ring_task = \
                tasks.add_ring_info.apply_async(
                    (new_ring_json, cluster_id))
            add_ring_result = add_ring_task.get()
            # add_ring_result = add_ring_task.get()
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
def add_defined_option_ring(request):
    if request.method == "POST":
        option_name = request.POST['optionName']
        option_full_name = request.POST['optionFullName']
        option_description = request.POST['optionDescription']
        duplicate_factor = int(request.POST['optionDuplicateFactor'])
        capacity_limit = float(request.POST['optionCapacityLimit'])
        read10mb_limit = float(request.POST['optionRead10mb'])
        write10mb_limit = float(request.POST['optionWrite10mb'])
        read128k_limit = float(request.POST['optionRead128k'])
        write128k_limit = float(request.POST['optionWrite128k'])
        compatible_clusters = get_compatible_clusters(
            option_name, capacity_limit,
            read10mb_limit, write10mb_limit,
            read128k_limit, write128k_limit
        )
        compatible_names = []
        for cluster in compatible_clusters:
            compatible_names.append(cluster.name)
        if len(compatible_clusters) < duplicate_factor:
            return JsonResponse({'create_result': 'false',
                                 'message': 'Failed to create opion ring ' + option_name + '. ' +
                                            'Reason: Not enough clusters compatible with input parameters!'},
                                status=200)
        else:

            # def create_core_ring(request, name, ring_type, version, full_name,
            #                      description):
            # create defined option ring
            ring_type = 'object_defined'
            create_ring_result = create_defined_option_ring(
                option_name, option_full_name, option_description, ring_type,
                1, compatible_clusters, duplicate_factor)

            if create_ring_result == True:
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
