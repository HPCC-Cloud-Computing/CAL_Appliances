import hashlib
import random
from math import floor

from django.conf import settings
from ..chord.node import Node


class Ring(object):
    def __init__(self, username, clouds):
        self.id = int(hashlib.md5(username).hexdigest(),
                      16) % settings.RING_SIZE
        self.username = username
        self.size = settings.RING_SIZE
        self.nodes = []
        # clouds = [cloud1, cloud2, cloud3...]
        # # cloud1 = Cloud(type, config, address)
        # # cloud1 is an instance of class Cloud
        self.clouds = clouds
        self.generate_ring()
        self._generate_cloud_refs_to_node()
        # self.write_ring_info()

    # def write_ring_info(self):
    #     with open('/tmp/' + str(self.id), 'wb+') as f:
    #         for node in self.nodes:
    #             f.write('####' + str(node.id) + '\n')
    #             for cloud in node.clouds:
    #                 f.write(cloud.name + '\n')

    def generate_ring(self):
        """Generate ring"""
        first_node = Node(self.username, 0)
        first_node.join(first_node)
        self.nodes.append(first_node)
        for id in range(1, settings.RING_SIZE):
            node = Node(self.username, id)
            node.join(first_node)
            self.nodes.append(node)

    def _calculate_refs_cloud(self):
        """Calculate number of references per cloud."""
        total_refs = settings.RING_SIZE * settings.REPLICA_NUM
        self._set_weight_cloud()
        _tmp_sum = 0
        for cloud in self.clouds:
            cloud.num_of_refs = int(floor(cloud.weight * total_refs))
            _tmp_sum += cloud.num_of_refs
        # Re-check
        if _tmp_sum != total_refs:
            rand_elm = random.randrange(0, len(self.clouds))
            self.clouds[rand_elm].num_of_refs += total_refs - _tmp_sum

    def _generate_cloud_refs_to_node(self):
        self._calculate_refs_cloud()
        node_ref_list = [i for i in range(0, settings.RING_SIZE)]
        remain_nodes = [i for i in range(0, settings.RING_SIZE)]
        random.shuffle(remain_nodes)
        for cloud in self.clouds:
            if len(remain_nodes) < cloud.num_of_refs:
                selected_nodes = remain_nodes
                pick_missing_node_list = []
                for i in node_ref_list:
                    if i not in selected_nodes:
                        pick_missing_node_list.append(i)
                random.shuffle(pick_missing_node_list)
                missing_node_num = cloud.num_of_refs - len(selected_nodes)
                old_selected_nodes = list(selected_nodes)
                selected_nodes.extend(pick_missing_node_list[0:missing_node_num])
                remain_nodes = pick_missing_node_list[missing_node_num:]
                remain_nodes.extend(old_selected_nodes)
            else:
                selected_nodes = remain_nodes[0:cloud.num_of_refs]
                remain_nodes = remain_nodes[cloud.num_of_refs:]
            # Get number of ring node, then equal it with cloud.num_of_refs
            for i in range(0, cloud.num_of_refs):
                # set selected_node to reference to this cloud
                selected_node = self.nodes[selected_nodes[i]]
                selected_node.add_cloud_to_node(cloud)

    def lookup(self, key):
        """Lookup key"""
        if not (isinstance(key, int) or isinstance(key, long)):
            key = long(key)
        return self.nodes[0].find_successor(key)

    def _calculate_sum_quota(self):
        """Calculate sum quota"""
        sum_quotas = 0
        for cloud in self.clouds:
            sum_quotas += cloud.quota
        return sum_quotas

    def _set_weight_cloud(self):
        """Set cloud's weight:
        cloud.weight = cloud.quota / sum_quota"""
        sum_quotas = self._calculate_sum_quota()
        for cloud in self.clouds:
            cloud.set_weight(sum_quotas)
