from __future__ import absolute_import, unicode_literals
# import eventlet
# eventlet.monkey_patch()
import os
import sys
import time
import datetime
import django
import json
import memcache
import kazoo
from kazoo.client import KazooClient
from django.utils.timezone import tzinfo
from sys import path
from django.utils import timezone
from os.path import abspath, dirname

path.insert(0, os.getcwd())
# from mcos.settings.mcos_conf import PERIODIC_SEND_STATUS_TIME
# from mcos.settings.mcos_conf import PERIODIC_UPDATE_AND_POPULATE_RING
PERIODIC_UPDATE_AND_POPULATE_RING = 120
from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME
from mcos.settings.base import TIME_ZONE
from mcos_celery_server import tasks
from mcos.apps.utils.cache import MemcacheClient
from mcos.apps.utils.zk_client import ZkClient
from mcos.apps.utils.zk_client import LockManager
from mcos.apps.admin.shared_database.connection import SharedDatabaseConnection
from mcos_resolver_and_ring_server import tasks as ring_task

os.environ['DJANGO_SETTINGS_MODULE'] = 'mcos.settings'
django.setup()

from mcos.apps.admin.system.models import SystemCluster
from mcos.apps.admin.system.models import ObjectServiceInfo

# --- setup leader election process ---

election_path = '/election'

# add cluster_id + current proc_id as EPHEMERAL node in "/election" path
# in zookeeper server

# check if current node is leader node (node that has lowest id)
# if current node is leader node, do ring synchronizing operation

current_cluster = MCOS_CLUSTER_NAME

current_pid = os.getpid()

# gid of current process in zookeeper
election_id = current_cluster + str(current_pid)

zk = ZkClient()
zk.start()

zk.ensure_path(election_path)

create_node_result = zk.create(election_path + "/" + election_id,
                               ephemeral=True,
                               sequence=True)
leader_seq_number = 9999999999
current_seq_number = int(create_node_result[-10:])

node_set = zk.get_children(election_path)

# find leader sequence number find previous node sequence number
previous_seq_number = -1
previous_seq_node_path = ''

for node_path in node_set:
    check_seq_number = int(node_path[-10:])

    if check_seq_number < leader_seq_number:
        leader_seq_number = check_seq_number
    if check_seq_number < current_seq_number:
        if previous_seq_number < check_seq_number:
            previous_seq_number = check_seq_number
            previous_seq_node_path = node_path


def handle_leader_changed(event):
    try:
        global leader_seq_number
        global previous_seq_number
        global previous_seq_node_path

        leader_seq_number = 9999999999
        previous_seq_number = -1
        previous_seq_node_path = ''
        node_set = zk.get_children(election_path)
        for node_path in node_set:
            check_seq_number = int(node_path[-10:])
            if check_seq_number < leader_seq_number:
                leader_seq_number = check_seq_number
            if check_seq_number < current_seq_number:
                if previous_seq_number < check_seq_number:
                    previous_seq_number = check_seq_number
                    previous_seq_node_path = node_path
        if previous_seq_number != -1:
            prev_node = zk.get(election_path + "/" + previous_seq_node_path,
                               watch=handle_leader_changed)
    except Exception as e:
        print(e)


if previous_seq_number != -1:
    prev_node = zk.get(election_path + "/" + previous_seq_node_path,
                       watch=handle_leader_changed)


# --- end setup leader election process ---


def check_cluster_exist(check_cluster, updated_clusters):
    is_exist = False
    for cluster in updated_clusters:
        if cluster.id == check_cluster.id:
            is_exist = True
    return is_exist


# check if all data of this ring and pointed by
# this ring is synchronize done
# function check if a specific ring is synchronize data done
def check_populate_ring(check_ring_id):
    return True


def get_ring_info(ring, active_updated_cluster):
    ring_get_info_task = ring_task.get_ring_info.apply_async(
        (ring.id,), routing_key=active_updated_cluster.name + '.get_ring_info'
    )
    ring_data = ring_get_info_task.get()
    if ring_data != "error":
        return ring_data
    else:
        raise Exception("Error when get ring from active cluster")


def send_ring_data(ring_data, not_updated_cluster):
    send_ring_data_task = ring_task.add_ring_info.apply_async(
        (ring_data, not_updated_cluster.id),
        routing_key=not_updated_cluster.name + '.get_ring_info')
    send_result = send_ring_data_task.get()
    if send_result is True:
        return True
    else:
        print("Update cluster failed at cluster: " + not_updated_cluster.name)


# test leader election function
# def main():
#     not_exit = True
#     while not_exit:
#         try:
#             print("Current node:" + str(current_seq_number))
#             if current_seq_number == leader_seq_number:
#                 print("Current node is leader node: "
#                       + str(leader_seq_number))
#             else:
#                 print("Leader node: " + str(leader_seq_number))
#             print("Prev node: " + str(previous_seq_number))
#             print("Node set:")
#             print(zk.get_children(election_path))
#             print("")
#             time.sleep(2)
#         except Exception as e:
#             print(e)
#             # sys.exit(1)

def main():
    not_exit = True
    lock_manager = LockManager()
    shared_db_conn = None
    while not_exit:
        try:
            print(datetime.datetime.now())
            # print("Current node:" + str(current_seq_number))
            # if current node is leader node,
            # check populate ring and send ring to active cluster not updated
            if current_seq_number == leader_seq_number:
                shared_db_conn = SharedDatabaseConnection()
                rings = shared_db_conn.get_ring_list()
                cluster_set = shared_db_conn.get_cluster_list()
                for ring in rings:
                    updated_clusters = ring.updated_clusters
                    not_updated_clusters = []
                    for check_cluster in cluster_set:
                        if check_cluster_exist(check_cluster,
                                               updated_clusters) is not True:
                            not_updated_clusters.append(check_cluster)
                    if len(not_updated_clusters) == 0:
                        print("not_updated_cluster_number: " +
                              str(len(not_updated_clusters)))
                        # check if all data of this ring and pointed by
                        # this ring is synchronize done
                        if check_populate_ring(ring) is True:
                            pass
                            # unlock ring if current ring is locked
                            # lock path must be according ring version
                            lock_name = ring.name + '_' + str(ring.version)
                            # lock_manager = LockManager()
                            is_locked = lock_manager.get_ring_lock(lock_name)
                            if is_locked is not None:
                                print('release lock:' + lock_name)
                                lock_manager.release_ring_lock(lock_name)
                    else:
                        # get ring from a updated cluster which is active
                        active_updated_cluster = None
                        for check_cluster in updated_clusters:
                            cluster_status = SystemCluster.objects.filter(
                                id=check_cluster.id).first().status
                            if cluster_status == SystemCluster.ACTIVE:
                                active_updated_cluster = check_cluster
                                break
                        if active_updated_cluster is not None:
                            ring_data = get_ring_info(ring,
                                                      active_updated_cluster)
                            # print(ring_data[:100])
                            for not_updated_cluster in not_updated_clusters:
                                not_updated_cluster_status = SystemCluster.objects. \
                                    filter(
                                    id=not_updated_cluster.id).first().status
                                if not_updated_cluster_status == SystemCluster.ACTIVE:
                                    send_ring_result = send_ring_data(
                                        ring_data, not_updated_cluster)
                                    if send_ring_result is True:
                                        shared_db_conn.add_updated_cluster(
                                            ring, not_updated_cluster)
                shared_db_conn.close()
            else:
                print("Leader node: " + str(leader_seq_number))
            print("Prev node: " + str(previous_seq_number))
            print("Current node: " + str(current_seq_number))
            print("Node set:")
            # print(zk.get_children(election_path))
            print("")
        except Exception as e:
            shared_db_conn.close()
            shared_db_conn = SharedDatabaseConnection()
            print(e)
            # sys.exit(1)
        time.sleep(PERIODIC_UPDATE_AND_POPULATE_RING)


# run main function of this process
main()
