import os

from calplus.client import Client
from calplus.provider import Provider


class Cloud(object):

    def __init__(self, name, type, address, config):
        self.name = name
        self.address = address
        self.type = type
        self.status = 'OK'
        self.provider = Provider(type, config)
        self.connector = Client(version='1.0.0', resource='object_storage',
                                provider=self.provider)

    def set_quota(self, username):
        """Return quota (unit - bytes)"""
        container_stat = self.connector.stat_container(username)
        for stat in container_stat.keys():
            if 'quota' in stat:
                self.quota = container_stat[stat]
        self.quota = long(8589934592)  # Unit: Bytes

    def set_usage(self, username):
        """Get used (unit- bytes)"""
        self.used = 0  # Unit: Bytes
        if self.type.lower() == 'openstack':
            for obj in self.connector.list_container_objects(username):
                self.used += obj['bytes']
        elif self.type.lower() == 'amazon':
            for obj in self.connector.list_container_objects(username)['Contents']:
                self.used += obj['Size']

    def check_health(self):
        """Check health - simple with ping"""
        response = os.system('ping -c 1 ' + self.address)
        if response == 0:
            self.status = 'OK'
        else:
            self.status = 'CORRUPTED'

    def set_weight(self, sum_quotas):
        self.set_quota()
        self.weight = self.quota / sum_quotas
