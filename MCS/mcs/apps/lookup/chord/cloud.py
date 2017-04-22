from __future__ import division

import os
from calplus.client import Client
from calplus.provider import Provider

from dashboard.utils import sizeof_fmt


class Cloud(object):
    def __init__(self, username, name, type, address, config):
        self.name = name
        self.address = address
        self.type = type
        self.status = 'OK'
        self.username = username
        self.provider = Provider(type, config)
        self.connector = Client(version='1.0.0', resource='object_storage',
                                provider=self.provider)
        # Set quota
        self.set_quota()

    def set_quota(self):
        """Return quota (unit - bytes)"""
        try:
            self.connector.stat_container(self.username)
        except:
            self.connector.create_container(self.username)
        container_stat = self.connector.stat_container(self.username)
        for stat in container_stat.keys():
            if 'quota' in stat:
                self.quota = container_stat[stat]
        self.quota = long(8589934592)  # Unit: Bytes

    def set_usage(self):
        """Get used (unit- bytes)"""
        self.used = 0  # Unit: Bytes
        if self.type.lower() == 'openstack':
            for obj in self.connector.list_container_objects(self.username):
                self.used += obj['bytes']
        elif self.type.lower() == 'amazon':
            for obj in self.connector.list_container_objects(self.username,
                                                             prefix='',
                                                             delimiter='')['Contents']:
                self.used += obj['Size']

    def set_used_rate(self):
        """Set used rate = used/quota"""
        self.set_usage()
        used = sizeof_fmt(float(self.used))
        quota = sizeof_fmt(float(self.quota))
        self.used_rate = used + '/' + quota

    def check_health(self):
        """Check health - simple with ping"""
        response = os.system('ping -c 1 ' + self.address)
        if response == 0:
            self.status = 'OK'
        else:
            self.status = 'CORRUPTED'

    def set_weight(self, sum_quotas):
        self.weight = float(self.quota / sum_quotas)
