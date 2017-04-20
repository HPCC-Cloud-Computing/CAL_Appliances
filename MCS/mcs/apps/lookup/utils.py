import json
import logging
import os

import dill as pickle
from lookup.chord.cloud import Cloud

LOG = logging.getLogger(__name__)


def load_cloud_configs(username, json_data):
    """Load cloud configs from json"""
    cloud_configs = json.load(json_data)
    clouds = list()
    for cloud_name in cloud_configs.keys():
        cloud = Cloud(username, cloud_name,
                      cloud_configs[cloud_name]['type'],
                      cloud_configs[cloud_name]['address'],
                      cloud_configs[cloud_name]['config'])
        clouds.append(cloud)
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
        pickle.dump(obj, open(path, 'wb'), pickle.HIGHEST_PROTOCOL, byref=True)


def load(path):
    """Load Classifier object from pickle file"""
    if not os.path.isfile(path):
        LOG.info('File doesnt existed!')
        raise IOError()
    else:
        return pickle.load(open(path, 'rb'))
