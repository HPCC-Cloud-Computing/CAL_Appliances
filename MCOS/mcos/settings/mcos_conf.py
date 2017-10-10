from __future__ import absolute_import, unicode_literals

MCOS_IP = '127.0.0.1'
MCOS_PORT = '8000'
# if current node is the first node of system, set to it connect to itself
# else, fill this option by list of IP of nearest node of it.
# CONNECT_SERVER = ['192.168.50.1:8000']
CONNECT_SERVER = '127.0.0.1:8000'
MCOS_CLUSTER_NAME = 'hp-proBook-450'
PERIODIC_CHECK_STATUS_TIME = 10
PERIODIC_SEND_STATUS_TIME = 4
MESSAGE_QUEUE_IP = '172.20.5.1'

MEMCACHED_IP = '172.20.6.1'
MEMCACHED_PORT = 11211

