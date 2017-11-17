from __future__ import absolute_import
from django.contrib import messages
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME
from ..system.models import SystemCluster
from mcos.apps.authentication.auth_plugins.decorators import login_required
from mcos import utils as mcos_utils


# from ...lookup import utils as lookup_utils
# from .. import utils as dashboard_utils

def set_context(view_context=None):
    context = {
        'cluster_name': MCOS_CLUSTER_NAME,
        'user_name': 'Administrator 1'
    }
    if view_context is not None:
        context.update(view_context)
    return context


@login_required(role='admin')
def dashboard_overview(request):
    clusters = SystemCluster.objects.all()
    total_active_clusters = 0
    total_clusters = len(clusters)
    for cluster in clusters:
        if cluster.status == SystemCluster.ACTIVE:
            total_active_clusters += 1
    active_cluster_percent = str(total_active_clusters * 100 / total_clusters) + '%'
    rings = mcos_utils.get_shared_value('rings')
    total_core_rings = 0
    total_option_rings = 0
    for ring in rings:
        if ring['ring_type'] == 'account' or ring['ring_type'] == 'container' \
                or ring['ring_type'] == 'group_resolver':
            total_core_rings += 1
        else:
            total_option_rings += 1
    return render(request, 'admin/dashboard/index.html',
                  set_context({
                      'total_clusters': total_clusters,
                      'total_active_clusters': total_active_clusters,
                      'active_cluster_percent': active_cluster_percent,
                      'total_core_rings': total_core_rings,
                      'total_option_rings': total_option_rings
                  }))


@login_required(role='admin')
def cluster_management(request):
    return render(request, 'admin/dashboard/cluster_management.html',
                  set_context())


# account ring in memcache structure:
# account_ring = {
#                   'replica_number':4,
#                   'cluster_list':[],
#                   'rings':[]
#                }
# container ring in memcache structure:
# container_ring = {
#                   'cluster_list':[],
#                   'rings':[]
#                }
@login_required(role='admin')
def core_ring(request):
    # currently supported for one ring
    # multi ring version is implemented in next phase
    account_clusters = []
    container_clusters = []
    rings = mcos_utils.get_shared_value('rings')
    account_ring_info = None
    container_ring_info = None
    group_resolver_ring_info = None
    for ring in rings:
        if ring['ring_type'] == 'account':
            account_ring_info = ring
        if ring['ring_type'] == 'container':
            container_ring_info = ring
        if ring['ring_type'] == 'group_resolver':
            group_resolver_ring_info = ring
    if account_ring_info is not None:
        account_ring_str = mcos_utils.get_shared_value('ring_account_1')
        account_ring_info = json.loads(account_ring_str)
        cluster_ids = ''
        for cluster_id in account_ring_info['ring_clusters']:
            cluster_ids += (cluster_id + ':')
        cluster_ids = cluster_ids[:-1]
        account_ring_info['cluster_ids'] = cluster_ids

    if container_ring_info is not None:
        container_ring_str = mcos_utils.get_shared_value('ring_container_1')
        container_ring_info = json.loads(container_ring_str)
        cluster_ids = ''
        for cluster_id in container_ring_info['ring_clusters']:
            cluster_ids += (cluster_id + ':')
        cluster_ids = cluster_ids[:-1]
        container_ring_info['cluster_ids'] = cluster_ids

    if group_resolver_ring_info is not None:
        group_resolver_ring_str = \
            mcos_utils.get_shared_value('ring_group_resolver_1')
        group_resolver_ring_info = json.loads(group_resolver_ring_str)
        cluster_ids = ''
        for cluster_id in group_resolver_ring_info['ring_clusters']:
            cluster_ids += (cluster_id + ':')
        cluster_ids = cluster_ids[:-1]
        group_resolver_ring_info['cluster_ids'] = cluster_ids
    # if account_ring_info is not None:
    #     account_clusters = account_ring_info['ring_clusters']
    # get more information about cluster from database

    # if container_ring_info is not None:
    #     container_ring = mcos_utils.get_shared_value('ring_container_1')
    #     if container_ring is not None:
    #         container_clusters = container_ring['ring_clusters']
    # get more information about cluster from database

    # account_clusters = [
    #     {
    #         'id': 'e97bf6aa-7309-43fa-9aed-7ca8f7a2d01b',
    #         'name': 'CAL-1',
    #         'address': '127.0.0.1:8001',
    #         'status': '1',
    #         'last_update':'2017-10-11 20:40:25.878729+00:00'
    #     },
    #     {
    #         'id': '1297bf6aa-7309-43fa-9aed-7ca8f7a2d01b',
    #         'name': 'CAL-2',
    #         'address': '127.0.0.1:8002',
    #         'status': '1',
    #         'last_update': '2017-10-11 20:40:25.878729+00:00'
    #     },
    # ]
    # container_clusters = [
    #     {
    #         'id': 'e97bf6aa-7309-43fa-9aed-7ca8f7a2d01b',
    #         'name': 'CAL-1',
    #         'address': '127.0.0.1:8001',
    #         'status': '1',
    #         'last_update': '2017-10-11 20:40:25.878729+00:00'
    #     },
    #     {
    #         'id': '1297bf6aa-7309-43fa-9aed-7ca8f7a2d01b',
    #         'name': 'CAL-2',
    #         'address': '127.0.0.1:8002',
    #         'status': '1',
    #         'last_update': '2017-10-11 20:40:25.878729+00:00'
    #     },
    # ]
    return render(request, 'admin/dashboard/core_ring.html',
                  set_context({
                      'account_info': account_ring_info,
                      'container_info': container_ring_info,
                      'group_resolver_info': group_resolver_ring_info
                  }))


# option-object-management
@login_required(role='admin')
def options_management(request):
    rings = mcos_utils.get_shared_value('rings')
    defined_rings = []
    custom_rings = []
    no_option_rings = None

    # check if defined option rings not exist
    enable_defined_ring = None
    total_defined_ring_not_create = 4
    not_defined_opt_rings = {
        'optimize_big': True,
        'economy_big': True,
        'optimize_small': True,
        'economy_small': True
    }

    for ring in rings:
        if 'object' in ring['ring_type']:
            if 'object_defined' == ring['ring_type']:
                total_defined_ring_not_create -= 1
                for key, value in not_defined_opt_rings.iteritems():
                    if ring['name'] == key:
                        not_defined_opt_rings.pop(key, None)
                        break
                ring_str = mcos_utils.get_shared_value('ring_' + ring['name'] + '_' + str(ring['version'][0]))
                ring_info = json.loads(ring_str)
                defined_rings.append(ring_info)
            if 'object_custom' == ring['ring_type']:
                ring_str = mcos_utils.get_shared_value('ring_' + ring['name'] + '_' + str(ring['version'][0]))
                ring_info = json.loads(ring_str)
                custom_rings.append(ring_info)
    if len(defined_rings) + len(custom_rings) == 0:
        no_option_rings = True
    if total_defined_ring_not_create > 0:
        enable_defined_ring = True

    return render(request, 'admin/dashboard/options_management.html',
                  set_context({
                      'total_option_rings': len(defined_rings) + len(custom_rings),
                      'defined_rings': defined_rings,
                      'custom_rings': custom_rings,
                      'no_option_rings': no_option_rings,
                      'not_defined_opt_rings': not_defined_opt_rings,
                      'enable_defined_ring': enable_defined_ring
                  }))


@login_required(role='admin')
def get_clusters_ids(request):
    if request.method == 'GET':
        clusters = []
        total_cluster = int(request.GET['cluster_id_number'])
        for i in range(0, total_cluster):
            cluster_id = request.GET['cluster_id_' + str(i)]
            clusters.append(
                SystemCluster.objects.filter(id=cluster_id).get().to_dict()
            )
        return JsonResponse({'cluster_list': clusters})


@login_required(role='admin')
def get_ring_clusters(request):
    if request.method == 'GET':
        clusters = []
        ring_name = request.GET['ring_name']
        ring_version = request.GET['ring_version']
        ring_str = mcos_utils.get_shared_value('ring_' + ring_name + '_' + str(ring_version))
        ring_info = json.loads(ring_str)
        for key, value in ring_info['ring_clusters'].iteritems():
            cluster_id = key
            clusters.append(
                SystemCluster.objects.filter(id=cluster_id).get().to_dict()
            )
        return JsonResponse({'cluster_list': clusters})


def clusters_tbl_api(request):
    cluster_dict_list = []
    cluster_info_list = SystemCluster.objects.all()
    for cluster_info in cluster_info_list:
        cluster_dict_list.append(cluster_info.to_dict())
    return JsonResponse({'cluster_list': cluster_dict_list})


def test_user_role(request):
    return render(request, 'admin_dashboard/home.html', {})
