import memcache
from mcos.settings import MEMCACHED_IP, MEMCACHED_PORT


class MemcacheClient(memcache.Client):
    def __init__(self):
        super(MemcacheClient, self).__init__([(MEMCACHED_IP, MEMCACHED_PORT)])

    def get_data(self, key_name):
        return self.get(key_name)

    def set_data(self, key_name, value):
        return self.set(key_name, value)
