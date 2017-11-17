import hashlib
import os
import memcache
from kazoo.client import KazooClient
from mcos.settings import ZOOKEEPER_IP, ZOOKEEPER_PORT
from mcos.apps.utils import cache
from kazoo.exceptions import NodeExistsError
from django.conf import settings
ZOOKEEPER_ADDR = ZOOKEEPER_IP + ":" + ZOOKEEPER_PORT


# MEMCACHED_ADDR = MEMCACHED_IP + MEMCACHED_PORT


class LockManager:
    def __init__(self):
        self.zk_client = KazooClient(hosts=ZOOKEEPER_ADDR)
        self.zk_client.start()
        self.lock_path = '/lock'

    @staticmethod
    def get_current_cluster_id():
        memcache_client = cache.MemcacheClient()
        cluster_id = memcache_client.get('current_cluster_id')
        if cluster_id is None:
            current_cluster = SystemCluster.objects.filter(
                name=MCOS_CLUSTER_NAME).first()
            memcache_client.set('current_cluster_id', str(current_cluster.id))
            cluster_id = current_cluster.id
        return cluster_id

    def get_lock(self, lock_absolute_name):
        lock_path_exist = self.zk_client.exists(lock_absolute_name)
        if lock_path_exist is not None:
            lock_data = self.zk_client.get(lock_absolute_name)
            zk_lock_cluster_id = lock_data[0]
            if len(zk_lock_cluster_id) > 0:
                return lock_data
            else:
                return None
        else:
            return None

    def set_lock(self, lock_absolute_name, value):
        try:
            self.zk_client.create(lock_absolute_name, value)
            return True
        except NodeExistsError as e:
            # print(e)
            return False

    def acquire_ring_lock(self, lock_name):
        ring_lock_path = self.lock_path + '/ring'
        lock_absolute_name = ring_lock_path + "/" + lock_name
        self.zk_client.ensure_path(ring_lock_path)
        ring_lock = self.get_lock(lock_absolute_name)
        if ring_lock is not None:
            return False
        else:
            cluster_id = LockManager.get_current_cluster_id()
            # warning: in HA-environment, lock must be cluster_id+process_id
            return self.set_lock(lock_absolute_name, cluster_id)

            # def acquire_lock(self,lock_name):
            #
            #     cluster_id = get_current_cluster_id()
            #     # Ensure a path, create if necessary
            #     zk.ensure_path(lock_path)

    def get_ring_lock(self, lock_name):
        ring_lock_path = self.lock_path + '/ring'
        lock_absolute_name = ring_lock_path + "/" + lock_name
        self.zk_client.ensure_path(ring_lock_path)
        return self.get_lock(lock_absolute_name)

    def release_ring_lock(self, lock_name):
        ring_lock_path = self.lock_path + '/ring'
        lock_absolute_name = ring_lock_path + "/" + lock_name
        self.zk_client.ensure_path(ring_lock_path)
        ring_lock = self.get_lock(lock_absolute_name)
        if ring_lock is not None:
            self.zk_client.delete(lock_absolute_name)

    def close(self):
        self.zk_client.close()


class ZkClient(KazooClient):
    def __init__(self):
        super(ZkClient, self).__init__(hosts=ZOOKEEPER_ADDR)
