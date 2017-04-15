import os

from calplus.client import Client
from calplus.provider import Provider


class Cloud(object):
    def __init__(self, name, type, address, config):
        self.name = name
        self.address = address
        self.status = 'OK'
        self.provider = Provider(type, config)
        self.connector = Client(version='1.0.0', resource='object_storage',
                                provider=self.provider)

    def get_quota(self, username):
        """Return quota (unit - bytes)"""
        # TODO:
        # Set metadata 'quota' to container:
        container_stat = self.connector.stat_container(username)
        for stat in container_stat.keys():
            if 'quota' in stat:
                return container_stat[stat]
        return None

    def get_usage(self, username):
        """Get used (unit- bytes)"""
        # TODO:
        # Set metadata 'used' to container:
        # used = sum(object.content) for object in objects_in_container
        # update 'used' when upload and delete object.
        container_stat = self.connector.stat_container(username)
        for stat in container_stat.keys():
            if 'used' in stat:
                return container_stat[stat]
        return None

    def check_health(self):
        """Check health - simple with ping"""
        response = os.system('ping -c 1 ' + self.address)
        if response == 0:
            self.status = 'OK'
        else:
            self.status = 'CORRUPTED'

    def set_weight(self, sum_quotas):
        self.get_quota()
        self.weight = self.quota / sum_quotas
