import json
import logging
import pickle
import os
from calplus.client import Client
from django.contrib import messages

from lookup.chord.cloud import Cloud

LOG = logging.getLogger(__name__)


def load_cloud_configs(request, username, json_data):
    """Load cloud configs from json"""
    try:
        cloud_configs = json.load(json_data)
        clouds = list()
        for cloud_name in cloud_configs.keys():
            cloud = Cloud(username, cloud_name,
                          cloud_configs[cloud_name]['type'],
                          cloud_configs[cloud_name]['address'],
                          cloud_configs[cloud_name]['config'])
            clouds.append(cloud)
    except ValueError:
        messages.error(request, 'Your config is not valid!')
        clouds = None
    return clouds


def check_diff_seq_elements(data):
    """Check if 3 sequential elements in list are diff
    For e.x: data = [1, 2, 3] -> return True.
    data = [1,2,3] -> return False
    """
    seq_list = zip(data[:-1], data[1:], data[2:])
    for three_ele in seq_list:
        if three_ele[0] == three_ele[1] or three_ele[1] == three_ele[2] or three_ele[0] == three_ele[2]:
            return False
    return True


def save(obj, path):
    """Save Classifier object to pickle file."""
    if os.path.isfile(path):
        LOG.info('File existed! Use load() method.')
    else:
        pickle.dump(obj, open(path, 'wb'),
                    protocol=pickle.HIGHEST_PROTOCOL)


def load(path):
    """Load Classifier object from pickle file"""
    if not os.path.isfile(path):
        LOG.info('File doesnt existed!')
        raise IOError()
    else:
        return pickle.load(open(path, 'rb'))


def set_quota_cloud(cloud):
    """Set cloud's quota"""
    connector = Client(version='1.0.0', resource='object_storage',
                       provider=cloud.provider)
    try:
        connector.stat_container(cloud.username)
    except Exception:
        connector.create_container(cloud.username)
    container_stat = connector.stat_container(cloud.username)
    for stat in container_stat.keys():
        if 'quota' in stat:
            cloud.quota = container_stat[stat]
    cloud.quota = long(8589934592)  # Unit: Bytes


def set_usage_cloud(cloud):
    """Set clouds's used space"""
    connector = Client(version='1.0.0', resource='object_storage',
                       provider=cloud.provider)
    cloud.used = 0  # Unit: Bytes
    if cloud.type.lower() == 'openstack':
        for obj in connector.list_container_objects(cloud.username):
            cloud.used += obj['bytes']
    elif cloud.type.lower() == 'amazon':
        list_objects = connector.list_container_objects(cloud.username,
                                                        prefix='',
                                                        delimiter='')
        if 'Contents' in list_objects:
            for obj in list_objects['Contents']:
                cloud.used += obj['Size']
