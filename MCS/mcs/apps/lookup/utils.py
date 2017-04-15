import json

from lookup.chord.cloud import Cloud


def load_cloud_configs(json_data):
    """Load cloud configs from json"""
    cloud_configs = json.load(json_data)
    clouds = list()
    for cloud_name in cloud_configs.keys():
        cloud = Cloud(cloud_name, cloud_configs[cloud_name]['type'],
                      cloud_configs[cloud_name]['address'],
                      cloud_configs[cloud_name]['config'])
        clouds.append(cloud)
    return clouds
