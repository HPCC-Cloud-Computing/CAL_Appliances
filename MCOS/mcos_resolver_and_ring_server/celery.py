from __future__ import absolute_import, unicode_literals
import os
import sys
import time
import django
from sys import path
from os.path import abspath, dirname
from celery import Celery
from mcos.apps.utils.cache import MemcacheClient
from .ring_db import Session as LocalRingDbSession, Ring as LocalRing

app = Celery('mcos_resolver_and_ring_server')
app.config_from_object('mcos_resolver_and_ring_server.settings')


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)


def load_rings():
    memcache_client = MemcacheClient()
    current_mem_ring_list = memcache_client.get('rings')

    ring_list = []
    local_ring_conn = LocalRingDbSession()
    rings = local_ring_conn.query(LocalRing).all()
    print(len(rings))
    for ring in rings:
        print(ring.name)
        # check if ring is exist in ring_list
        exist_ring_info = None
        for loaded_ring_info in ring_list:
            if ring.name == loaded_ring_info['name']:
                exist_ring_info = loaded_ring_info
                break
        if exist_ring_info is None:
            ring_info = {'name': ring.name, 'version': [ring.version, ], 'ring_type': ring.ring_type}
            ring_list.append(ring_info)
        else:
            exist_ring_info['version'].append(ring.version)
            # load ring file to memcache
    memcache_client.set('rings', ring_list)
    for ring in rings:
        with open('rings/' + str(ring.name) + '_' +
                          str(ring.version) + '.txt', 'r') as ring_file:
            ring_data = ring_file.read()
            memcache_client.set('ring_' + str(ring.name) + '_' +
                                str(ring.version), ring_data)

    local_ring_conn.close()
    # if current_mem_ring_list is None:
    #     ring_list = []
    #     local_ring_conn = LocalRingDbSession()
    #     rings = local_ring_conn.query(LocalRing).all()
    #     # print(len(rings))
    #     for ring in rings:
    #         print(ring.name)
    #         # check if ring is exist in ring_list
    #         exist_ring_info = None
    #         for loaded_ring_info in ring_list:
    #             if ring.name == loaded_ring_info['name']:
    #                 exist_ring_info = loaded_ring_info
    #                 break
    #         if exist_ring_info is None:
    #             ring_info = {'name': ring.name, 'version': [ring.version, ], 'ring_type': ring.ring_type}
    #             ring_list.append(ring_info)
    #         else:
    #             exist_ring_info['version'].append(ring.version)
    #             # load ring file to memcache
    #     memcache_client.set('rings', ring_list)
    #     for ring in rings:
    #         with open('rings/' + str(ring.name) + '_' +
    #                           str(ring.version) + '.txt', 'r') as ring_file:
    #             ring_data = ring_file.read()
    #             memcache_client.set('ring_' + str(ring.name) + '_' +
    #                                 str(ring.version), ring_data)
    #
    #     local_ring_conn.close()


# before start celery_server, load rings to memcache
load_rings()
if __name__ == '__main__':
    app.start()
