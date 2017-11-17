# This ring is used for retrieval container list of a specified user

# get cluster list which are holding container list of this user
# return: cluster_id list


def find_clusters(user_id):
    clusters = []
    return clusters


def get_containers_from_cluster(cluster_id):
    return []


class GetContainerDataException(Exception):
    pass


def get_containers(user_id):
    is_collected_data = False
    container_list = []
    holding_clusters = find_clusters(user_id)
    for cluster in holding_clusters:
        try:
            container_list = get_containers(user_id)
            is_collected_data = True
        except Exception as e:
            print(e)
            print('Connection to cluster ' + str(cluster.cluster_id) +
                  ' is corrupted!')
    if is_collected_data:
        return container_list
    else:
        raise GetContainerDataException(
            'Can not connect to any cluster which are holding data!')
