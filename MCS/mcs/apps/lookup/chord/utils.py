from random import shuffle

from django.conf import settings


def decr(value, size):
    """Decrement"""
    if size <= value:
        return value - size
    else:
        return settings.RING_SIZE - (size - value)


def in_interval(val, left, right, equal_left=False, equal_right=False):
    """Check val is in (left, right) or not"""
    if (equal_left and val == left):
        return True

    if (equal_right and val == right):
        return True

    if (right > left):
        if (val > left and val < right):
            return True
        else:
            return False

    if (right < left):
        if (val < left):
            left = left - settings.RING_SIZE
        else:
            if (val > left):
                right = right + settings.RING_SIZE

        if (val > left and val < right):
            return True
        else:
            return False
    return True


REPLICA_FACTOR = 3


class CloudServer:
    def __init__(self, cloud_identity, reference_count):
        self.identity = cloud_identity
        self.reference_count = reference_count


class RingNode:
    def __init__(self, identity):
        self.identity = identity
        self.cloud_references = []
        pass

    def add_cloud_reference(self, cloud_server_ref):
        self.cloud_references.append(cloud_server_ref)


test_ring = [RingNode(0), RingNode(1), RingNode(2), RingNode(3), RingNode(4), RingNode(5), RingNode(6), RingNode(7),
             RingNode(8)]

# important! total cloud referrences in cloud_servers must equal node_number x REPLICA_FACTOR
test_cloud_servers = [CloudServer('c1', 6), CloudServer('c2', 3), CloudServer('c3', 4), CloudServer('c4', 4),
                      CloudServer('c5', 7), CloudServer('c6', 3)]


def assign_cloud_ref_to_nodes(ring, cloud_servers):
    # initial first selected list for first cloud
    node_reference_list = [i for i in range(0, len(ring))]

    remain_nodes = [i for i in range(0, len(ring))]
    shuffle(remain_nodes)

    for cloud_server in cloud_servers:
        if len(remain_nodes) < cloud_server.reference_count:

            selected_nodes = remain_nodes
            pick_missing_node_list = []
            for i in node_reference_list:
                if i not in selected_nodes:
                    pick_missing_node_list.append(i)
            shuffle(pick_missing_node_list)
            missing_node_number = cloud_server.reference_count - len(selected_nodes)

            old_selected_nodes = list(selected_nodes)
            selected_nodes.extend(pick_missing_node_list[0:missing_node_number])
            remain_nodes = pick_missing_node_list[missing_node_number:]
            # according algorithm, these nodes in old_selected_nodes (state of selected_nodes before extend to pick missing
            # nodes) must be append to new remain_nodes
            remain_nodes.extend(old_selected_nodes)
        else:
            selected_nodes = remain_nodes[0:cloud_server.reference_count]
            remain_nodes = remain_nodes[cloud_server.reference_count:]
        # get number of ring node  equals this cloud_server reference count
        for i in range(0, cloud_server.reference_count):
            # set selected_node to reference to this cloud server, with cloud_servers[select_list[i]] is selected node
            selected_node = ring[selected_nodes[i]]
            selected_node.add_cloud_reference(cloud_server)
        selected_nodes = remain_nodes


assign_cloud_ref_to_nodes(test_ring, test_cloud_servers)

for node in test_ring:
    reference_info = ''
    for cloud_server_info in node.cloud_references:
        reference_info = reference_info + ' - ' + cloud_server_info.identity
    print('node: ' + str(node.identity) + ' - referrence clouds: ' + reference_info)
    print(" ")