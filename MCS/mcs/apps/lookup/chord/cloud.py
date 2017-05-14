from __future__ import division

import os
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
        self.num_of_refs = 0

    def set_used_rate(self):
        """Set used rate = used/quota"""
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
